import discord
import asyncio
import datetime
import sqlite3
import requests

from Database import DiscordDB

PROPERTY_LIST = [
    "commands_channel",
    "mod_commands_channel",
    "announcement_channel",
    "kick_warning_num",
    "ban_warning_num",
    "warning_reset_days",
    "banned_words",
    "timezone",
    "welcome_message",
    "leave_message"
    ]

#Helper functions
def is_numeric(ch):
    return ch in "1234567890"

def convertToOrdinal(num: int):
    num = str(num)
    if(num[-1] == '1'):
        return num+"st"
    elif(num[-1] == '2'):
        return num+"nd"
    elif(num[-1] == '3'):
        return num+"rd"
    return num+"th"

def convertChannelStringToInt(channel_string: str):
    channel_string = channel_string.replace("<#","").replace(">","")
    try:
        return int(channel_string)
    except ValueError:
        return None

def convertMemberMentiontoInt(mention: str):
    mention = mention.replace("<@","").replace(">","")
    try:
        return int(mention)
    except ValueError:
        return None


class MyClient(discord.Client):

    async def scanForDatabase(self,message):
        #self.db.start()

        isdm = type(message.channel) == discord.DMChannel

        if(not self.db.messageExists(message.id) and not isdm): # Check for new message
            await self.addMessage(message)
        elif(not self.db.dmMessageExists(message.id) and isdm): # Check for new DM
            await self.addDMMessage(message)

        self.db.commit()

    #ON REACTION ADD
    async def on_raw_reaction_add(self,raw_reaction):
        #self.db.start()
        if(self.get_channel(raw_reaction.channel_id) != None):
            await self.addRawReaction(raw_reaction)
            self.db.commit()



    #ON MEMBER JOIN
    async def on_member_join(self,member):
        if(self.db.memberExists(member.id,member.guild.id)):
            self.db.updateMemberIsInGuild(member.id,member.guild.id,0)
        else:
            if(not self.userExists(member.id)):
                self.addUser(member)
            self.addMember(member)
        self.db.commit()
        try:
            msg = self.db.getGuildPropertyValue(member.guild.id,"welcome_message")
            if(msg != None):
                msg = msg.replace("%u",str(member)).replace("%m",member.mention)
                await member.send(msg)
        except discord.errors.Forbidden:
            pass

    #ON MEMBER LEAVE
    async def on_member_remove(self,member):
        self.db.updateMemberIsInGuild(member.id,member.guild.id,1)
        self.db.commit()

        if(member.guild.system_channel != None and member.guild.system_channel.permissions_for(member.guild.me).send_messages):
            msg = self.db.getGuildPropertyValue(member.guild.id,"leave_message")
            if(msg != None):
                msg = msg.replace("%u",str(member))
                await member.guild.system_channel.send(msg)

    #ON MEMBER UPDATE
    async def on_member_update(self,before,after):
        for act in after.activities:
            print(str(act))
            if(type(act) == discord.Spotify):
                print("Someone is listening to",act.title)
                if(act.track_id != self.db.getUserLastListenedTo(after.id)):
                    if(not self.db.spotifySongExists(act.track_id)):
                        
                        print("New song:",act.title,"-",act.track_id)
                        data = requests.get(act.album_cover_url).content
                        next_id = self.db.getMaxFileID()+1
                        if(not self.db.fileExists('album',None,data)):
                            self.db.insertFile(next_id,"album",None,act.album,"jfif",data)
                        else:
                            next_id = self.db.getFileID("album",None,data)

                        self.db.insertSpotifySong(act.track_id,act.title,act.artist,act.album,next_id)
                    else:
                        self.db.incrementSongListenCount(act.track_id)
                    self.db.updateUserLastListenedTo(after.id,act.track_id)
        self.db.commit()



    #ON MESSAGE
    async def on_message(self,message):
        #print(message.content)
        await self.scanForDatabase(message)
        
        if(message.content.startswith("/")):
            await self.process_commands(message)



    #PROCESS COMMANDS
    async def process_commands(self,message):
        command = message.content.split()[0].lower()
        #Command List Here
        if(command == "/help"):
            await self.help(message)
        elif(command == "/warn"):
            await self.warn(message)
        elif(command == "/forgive"):
            await self.forgive(message)
        elif(command == "/property"):
            await self.view_property(message)
        elif(command == "/set"):
            await self.set_property(message)

    #COMMANDS
    async def help(self,message):
        await message.channel.send("Stay tuned for more details!")

    async def warn(self,message):
        command = message.content.split()

        if(not message.author.guild_permissions.ban_members):
            return

        if(len(command) < 3):
            await message.channel.send("Invalid Usage. Correct usage:```/warn @<member> <reason>```")
            return
        kick_num = self.db.getGuildPropertyValue(message.guild.id,"kick_warning_num")
        if(kick_num != None and not message.guild.me.guild_permissions.kick_members):
            await message.channel.send("Cannot issue warning. The server is currently set to kick members after "+str(kick_num)+" warnings. This means I need the Kick Members permission to issue warnings. Either use `/set kick_warning_num 0` to set the number to 0, or give me the permission.")
            return
        ban_num = self.db.getGuildPropertyValue(message.guild.id,"ban_warning_num")
        if(ban_num != None and not message.guild.me.guild_permissions.ban_members):
            await message.channel.send("Cannot issue warning. The server is currently set to ban members after "+str(ban_num)+" warnings. This means I need the Ban Members permission to issue warnings. Either use `/set ban_warning_num 0` to set the number to 0, or give me the permission.")
            return

        user_id = convertMemberMentiontoInt(command[1])
        if(user_id == None or self.get_user(user_id) == None):
            await message.channel.send("Error: That user cannot be found.")
            return

        reason = " ".join(command[2:])
        
        self.db.insertWarning(user_id,message.guild.id,message.created_at,reason)
        warns = self.db.getNumOfWarningsForMember(user_id,message.guild.id)
        user = self.get_user(user_id)
        self.db.updateMemberLastWarning(user_id,message.guild.id,)
        await message.channel.send(user.mention + " You have been issued a warning. This is your "+convertToOrdinal(warns)+" warning.")

        if(ban_num != None and warns >= ban_num and message.guild.me.guild_permissions.ban_members):
            await message.channel.send(user.mention + " has been banned for gathering too many warnings")
            await message.guild.ban(user,delete_message_days=0,reason = "User accrued too many warnings")
            self.db.updateMemberIsInGuild(user.id,message.guild.id,1)
            try:
                await message.author.send("You have been kicked for accruing too many warnings.")
            except discord.errors.Forbidden:
                pass
        elif(kick_num != None and warns == kick_num and message.guild.me.guild_permissions.kick_members):
            await message.channel.send(user.mention + " has been kicked for gathering too many warnings")
            await message.guild.kick(user,reason = "User accrued too many warnings")
            self.db.updateMemberIsInGuild(user.id,message.guild.id,1)
            try:
                await message.author.send("You have been banned for accruing too many warnings.")
            except discord.errors.Forbidden:
                pass


    async def forgive(self,message):
        command = message.content.split()

    async def view_property(self,message):
        command = message.content.split()
        if(not message.author.guild_permissions.manage_guild):
            return

        if(len(command) != 2):
            await message.channel.send("Invalid Usage. Correct usage:```/property <property>```")
            return

        if(command[1] == "all"):
            await message.channel.send("""You can set the following properties using `/set`:```
commands_channel :: The channel ID where normal users can use my commands.
mod_commands_channel :: The channel ID where moderators can use moderation commands.
announcement_channel :: The channel ID where I will send all server announcements.
kick_warning_num :: The number of warnings a user must accrue before they are kicked from the server. Set to 0 to disable.
ban_warning_num :: The number of warnings a user must accrue before they are banned from the server. Set to 0 to disable
warning_reset_days :: The number of days that must past for a user without gaining any new warnings for all old warnings to be forgiven. Set to 0 to disable.
banned_words :: A comma separated list of words and phrases that the bot will moderate for.
timezone :: The timezone of the server. This is currently unused.
welcome_message :: The message I will DM new members of the server when they join. Use %m to mention the user, and %u to use their username.
leave_message :: The message I will post to the announcement channel (if one is set) when a member leaves the server. Use %u to use the user's username
```""")
        elif(command[1] not in PROPERTY_LIST):
            await message.channel.send("Could not find server propety `"+command[1]+"`. Use `/property all` to view all properties I can set.")
        else:
            await message.channel.send("`"+command[1]+"` is currently set to `" + str(self.db.getGuildPropertyValue(message.guild.id,command[1]))+"`")

       
    async def set_property(self,message):
        command = message.content.split()

        if(not message.author.guild_permissions.manage_guild):
            return
        
        if(len(command) < 3):
            await message.channel.send("Invalid Usage. Correct usage:```/set <property> <value>```")
            return

        if(command[1] not in PROPERTY_LIST):
            await message.channel.send("Could not find server propety `"+command[1]+"`. Use `/property all` to view all properties I can set.")
            return

        # Check given property and value for data validation
        value = " ".join(command[2:])
        #try:
        #    value = int(value)
        #except ValueError:
        #    pass
        # Value type: channel id
        if(command[1] == "commands_channel" or command[1] == "mod_commands_channel" or command[1] == "announcement_channel"):
            value = convertChannelStringToInt(value)
            #print(value)
            channel = self.get_channel(value)
            if(value == None or channel == None):
                await message.channel.send("Invalid value. Value needs to be a valid channel ID or a channel mention (i.e., #general).")
                return
            if(not channel.permissions_for(channel.guild.me).send_messages):
                await message.channel.send("I have to be able to see and send messages in the channel you have chosen. Grant me that permission and then try the command again.")
                return

        # Value type: positive int
        elif(command[1] == "kick_warning_num" or command[1] == "ban_warning_num" or command[1] == "warning_reset_days"):
            try:
                value = int(value)
                if(value < 0):
                    raise ValueError
                elif(value == 0):
                    value = None
            except ValueError:
                await message.channel.send("Invalid value. Value must be a positive (or 0) integer.")
                return
            kick_num = self.db.getGuildPropertyValue(message.guild.id,"kick_warning_num")
            if(command[1] == "ban_warning_num" and kick_num != None and value != None and value <= kick_num):
                await message.channel.send("The amount of warnings to ban a user must be greater than the number of warnings to kick a user.")
                return

        # Value type: word or phrase
        elif(command[1] == "banned_words"):
            await message.channel.send("Still being implemented")
            return
        # Value type: timezone
        elif(command[1] == "timezone"):
            await message.channel.send("Still being implemented")
            return
        # Value type: Message string
        elif(command[1] == "welcome_message" or command[1] == "leave_message"):
            if(command[1] == "leave_message"):
                if(not message.guild.system_channel.permissions_for(message.guild.me).send_messages):
                    await message.channel.send("I need permission to send messages in "+message.guild.system_channel.mention+" to post leaving messages.")
                    return


        else:
            await message.channel.send("I shouldn't be here");

        self.db.updateGuildProperty(message.guild.id,command[1],value)
        self.db.commit()
        await message.channel.send("Successfully set " + command[1])



    #WHEN READY
    async def on_ready(self):
        await self.change_presence(activity=discord.Game(name = "In Development"))
        print("Successfully set Bot's game status")

        


    #CONNECTION
    async def on_connect(self):
        print("Bot has connected to server at time:",datetime.datetime.now())
        self.db = DiscordDB("./discord.db3")

        #self.db.start()

        for channel_pair in self.db.select('''SELECT channel_id,last_message FROM text_channel'''):
            
            print(channel_pair)
            channel = self.get_channel(channel_pair[0])
            while(channel == None):
                channel = self.get_channel(channel_pair[0])
            print(channel,type(channel))
            async for message in channel.history(limit = None,after = datetime.datetime.strptime(channel_pair[1],'%Y-%m-%d %H:%M:%S.%f') if channel_pair[1] != None else None):
                if(not self.db.messageExists(message.id)):
                    await self.addMessage(message)
    
        self.db.commit()
        print("Done scanning for changes")
    #DISCONNECTION
    #async def on_disconnect(self):
    #    print("Bot has disconnected from server at time:",datetime.now())


    async def addGuild(self,guild):
        print("New guild:",str(guild))
        # Add icon
        next_file_id = None
        if(guild.icon != None):
            data = await guild.icon_url_as(format=None,static_format='png',size=1024).read()
            next_file_id = self.db.getMaxFileID()+1
            if(not self.db.fileExists('guild_icon',guild.id,data)):
                self.db.insertFile(next_file_id,'guild_icon',guild.id,guild.name,'gif' if guild.is_icon_animated() else 'png',data)
        # Add guild
        if(not self.db.guildExists(guild.id)):
            self.db.insertGuild(guild.id,guild.name,next_file_id)
            self.db.addDefaultGuildProperties(guild.id)

        # Add Users and Members of server
        for member in guild.members:
            if(not self.db.userExists(member.id)):
                await self.addUser(self.get_user(member.id))                
            await self.addMember(member)
        
        # Add emojis of server
        for emoji in guild.emojis:
            if(not self.db.emojiExists(emoji.id)):
                await self.addEmoji(emoji)

        # Add channels of server
        for channel in guild.text_channels:
            await self.addTextChannel(channel)

    async def addUser(self,user):
        if(user == None):
            return
        print("New user:",str(user),user.id)
        # Add Avatar
        data = await user.avatar_url_as(format=None,static_format="png",size=1024).read()
        next_file_id = self.db.getMaxFileID()+1
        if(not self.db.fileExists('avatar',user.id,data)):
            self.db.insertFile(next_file_id,'avatar',user.id,str(user),'gif' if user.is_avatar_animated() else 'png',data)
        # Add User
        if(not self.db.userExists(user.id)):
            self.db.insertUser(user.id,user.name,user.discriminator,int(user.bot),next_file_id)
    
    async def addMember(self,member):
        # Add member
        if(not self.db.memberExists(member.id,member.guild.id)):
            self.db.insertMember(member.id,member.guild.id,member.nick,0)

    async def addTextChannel(self,channel):
        # Add guild
        if(not self.db.guildExists(channel.guild.id)):
            await self.addGuild(channel.guild)
        # Add channel
        if(not self.db.channelExists(channel.id)):
            print("New channel:",str(channel))
            self.db.insertTextChannel(channel.id,channel.guild.id,channel.name)
        # Add messages
        async for message in channel.history(limit = None):
            if(not self.db.messageExists(message.id)):
                await self.addMessage(message)

    async def addMessage(self,message):
        # Add channel
        if(not self.db.channelExists(message.channel.id)):
            await self.addTextChannel(message.channel)
        # Add User and Member
        if(not self.db.userExists(message.author.id)):
            await self.addUser(self.get_user(message.author.id))
        if(not self.db.memberExists(message.author.id,message.guild.id)):
            if(type(message.author) == discord.User): # Member is no longer in the server
                self.db.insertMember(message.author.id,message.guild.id,None,int(True))
            else:
                await self.addMember(message.author)
        # Add message
        if(not self.db.messageExists(message.id)):
            self.db.insertMessage(message.id,message.guild.id,message.channel.id,message.author.id,str(message.type).replace("MessageType.",""),message.content,str(message.created_at),1 if len(message.attachments) > 0 else 0)
        # Add reactions
        for reaction in message.reactions:
            await self.addReaction(reaction)
        # Add Attachments
        for attachment in message.attachments:
            #print("Attachment?")
            filename = attachment.filename.split('.')
            data = await attachment.read()
            if(not self.db.fileExists('attachment',message.id,data)):
                self.db.insertFile(self.db.getMaxFileID()+1,'attachment',message.id,".".join(filename[:-1]),filename[-1],data)
        # Update channel last message
        self.db.updateChannelLastMessage(message.channel.id,str(message.created_at))
        # Update user last message
        self.db.updateMemberLastMessage(message.author.id,message.guild.id,str(message.created_at))

    async def addDMMessage(self,message):
        # Add DM Message
        if(not self.db.dmMessageExists(message.id)):
            self.db.insertDMMessage(message.id,message.author.id,message.content,str(message.created_at),1 if len(message.attachments) > 0 else 0)
        for attachment in message.attachments:
            filename = attachment.filename.split('.')
            data = await attachment.read()
            if(not self.db.fileExists('dm_attachment',message.id,data)):
                self.db.insertFile(self.db.getMaxFileID()+1,'dm_attachment',message.id,".".join(filename[:-1]),filename[-1],data)

    async def addEmoji(self,emoji):
        # Check if Emoji or PartialEmoji
        next_file_id = None
        if(type(emoji) == discord.PartialEmoji):
            data = requests.get("https://cdn.discordapp.com/emojis/"+str(emoji.id)).content
            next_file_id = self.db.getMaxFileID()+1
            if(not self.db.fileExists('emoji',emoji.id,data)):
                self.db.insertFile(next_file_id,'emoji',emoji.id,emoji.name,'gif' if emoji.animated else 'png',data)
            else:
                next_file_id = self.db.getFileID('emoji',emoji.id,data)
            if(not self.db.emojiExists(emoji.id)):
                self.db.insertPartialEmoji(emoji.id,emoji.name,int(emoji.animated),next_file_id)

        else:
            # Add Guild
            if(not self.db.guildExists(emoji.guild_id)):
                await self.addGuild(emoji.guild)
            # Add emoji
            # Insert File
            next_file_id = self.db.getMaxFileID()+1
            data = await emoji.url.read()
            if(not self.db.fileExists('emoji',emoji.id,data)):
                self.db.insertFile(next_file_id,'emoji',emoji.id,emoji.name,'gif' if emoji.animated else 'png',data)
            else:
                next_file_id = self.db.getFileID('emoji',emoji.id,data)
            if(not self.db.emojiExists(emoji.id)):
                self.db.insertEmoji(emoji.id,emoji.guild_id,emoji.name,int(emoji.animated),next_file_id)

    async def addUnicodeEmoji(self,emoji):
        self.db.insertUnicodeEmoji(ord(emoji),emoji)

    async def addReaction(self,reaction):
        # Add Guild
        if(not self.db.guildExists(reaction.message.guild.id)):
            await self.addGuild(reaction.message.guild)
        # Add Channel
        if(not self.db.channelExists(reaction.message.channel.id)):
            await self.addTextChannel(reaction.message.channel)
        # Add Message
        if(not self.db.messageExists(reaction.message.id)):
            await self.addMessage(reaction.message)
        # Add Emoji
        # Check if emoji is a string
        if(type(reaction.emoji) == str):
            #print("Unicode")
            #print(ord(reaction.emoji))
            if(not self.db.emojiExists(ord(reaction.emoji[0]))):
                await self.addUnicodeEmoji(reaction.emoji[0])
        else:
            #print("Custom")
            #print(reaction.emoji.id,reaction.emoji.name)
            if(not self.db.emojiExists(reaction.emoji.id)):
                await self.addEmoji(reaction.emoji)
        try:
            async for user in reaction.users():
                # Add User
                if(not self.db.userExists(user.id)):
                    await self.addUser(user)
                # Add Reaction - note, the if is needed because of how reactions are stored
                if(type(reaction.emoji) == str):
                    if(not self.db.reactionExists(ord(reaction.emoji[0]),user.id,reaction.message.id)):
                        self.db.insertReaction(ord(reaction.emoji[0]),user.id,reaction.message.id)
                else:
                    if(not self.db.reactionExists(reaction.emoji.id,user.id,reaction.message.id)):
                        self.db.insertReaction(reaction.emoji.id,user.id,reaction.message.id)
        except discord.errors.HTTPException:
            print("404 Bad Request (error code: 10014): Unknown Emoji. Ignoring error for now and continuing.")

    async def addRawReaction(self,raw_reaction):
        # Add Guild
        if(not self.db.guildExists(raw_reaction.guild_id)):
            await self.addGuild(self.get_guild(raw_reaction.guild_id))
        # Add Channel
        if(not self.db.channelExists(raw_reaction.channel_id)):
            await self.addTextChannel(self.get_channel(raw_reaction.channel_id))
        # Add Message - No way to do this?
        #if(not self.db.messageExists(raw_reaction.message_id)):
        #
        # Add Emoji
        if(raw_reaction.emoji.is_unicode_emoji()):
            if(not self.db.emojiExists(ord(raw_reaction.emoji.name[0])) and self.db.messageExists(raw_reaction.message_id)):
                await self.addUnicodeEmoji(raw_reaction.emoji.name[0])
        else:
            if(not self.db.emojiExists(raw_reaction.emoji.id) and self.db.messageExists(raw_reaction.message_id)):
                await self.addEmoji(raw_reaction.emoji)
        # Add Reaction
        if(raw_reaction.emoji.is_unicode_emoji()):
            if(not self.db.reactionExists(ord(raw_reaction.emoji.name[0]),raw_reaction.user_id,raw_reaction.message_id)):
                self.db.insertReaction(ord(raw_reaction.emoji.name[0]),raw_reaction.user_id,raw_reaction.message_id)
        else:
            if(not self.db.reactionExists(raw_reaction.emoji.id,raw_reaction.user_id,raw_reaction.message_id)):
                self.db.insertReaction(raw_reaction.emoji.id,raw_reaction.user_id,raw_reaction.message_id)
    
        

        



try:
    file = open("TOKEN.txt",'r')
    TOKEN = file.read()
except FileNotFoundError:
    TOKEN = input("TOKEN file not found. Please enter the bot's token here: ")
    file = open("TOKEN.txt",'w')
    file.write(TOKEN)
file.close()
bot = MyClient()
bot.run(TOKEN)


