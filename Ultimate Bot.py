import discord
import asyncio
import datetime
import sqlite3

from Database import DiscordDB


class MyClient(discord.Client):

    async def scanForDatabase(self,message):
        #self.db.start()

        isdm = message.channel.type is discord.DMChannel

        if(not self.db.messageExists(message.id) and not isdm): # Check for new message
            await self.addMessage(message)
        elif(not self.db.dmMessageExists(message.id) and isdm): # Check for new DM
            await self.addDMMessage(message)

        self.db.commit()

    #ON REACTION ADD
    async def on_raw_reaction_add(self,raw_reaction):
        #self.db.start()
        await self.addRawReaction(raw_reaction)
        self.db.commit()


    #ON MESSAGE
    async def on_message(self,message):
        
        await self.scanForDatabase(message)
        
        if(message.content.startswith("/")):
            await self.process_commands(message)



    #PROCESS COMMANDS
    async def process_commands(self,message):
        command = message.content.split()[0].lower()
        #Command List Here
        if(command == "/help"):
            await self.help(message)


    async def help(self,message):
        await message.channel.send("I currently don't have any commands! I only watch right now. Stay tuned for more details!")


    #WHEN READY
    async def on_ready(self):
        await self.change_presence(activity=discord.Game(name = "game"))
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
            async for message in channel.history(limit = None,after = datetime.datetime.strptime(channel_pair[1],'%Y-%m-%d %H:%M:%S.%f')):
                if(not self.db.messageExists(message.id)):
                    await self.addMessage(message)
    
        self.db.commit()
    #DISCONNECTION
    #async def on_disconnect(self):
    #    print("Bot has disconnected from server at time:",datetime.now())


    async def addGuild(self,guild):
        # Add guild
        print("New guild:",str(guild))
        if(not self.db.guildExists(guild.id)):
            self.db.insertGuild(guild.id,guild.name)

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
        print("New user:",str(user),user.id)
        # Add User
        if(not self.db.userExists(user.id)):
            self.db.insertUser(user.id,user.name,user.discriminator,1 if user.bot else 0,sqlite3.Binary(await user.avatar_url.read()))
    
    async def addMember(self,member):
        # Add member
        if(not self.db.memberExists(member.id,member.guild.id)):
            self.db.insertMember(member.id,member.guild.id,member.nick)

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
        # Add message
        if(not self.db.messageExists(message.id)):
            self.db.insertMessage(message.id,message.guild.id,message.channel.id,message.author.id,str(message.type).replace("MessageType.",""),message.content,str(message.created_at),1 if len(message.attachments) > 0 else 0)
        # Add reactions
        for reaction in message.reactions:
            await self.addReaction(reaction)
        # Update channel last message
        self.db.updateChannelLastMessage(message.channel.id,str(message.created_at))

    async def addDMMessage(self,message):
        # Add DM Message
        if(not self.db.dmMessageExists(message.id)):
            self.db.insertDMMessage(message.id,message.author.id,message.content,str(message.created_at),1 if len(message.attachments) > 0 else 0)

    async def addEmoji(self,emoji):
        # Check if Emoji or PartialEmoji
        if(type(emoji) == discord.PartialEmoji):
            try:
                data = sqlite3.Binary(await emoji.url.read())
            except discord.errors.DiscordException:
                data = None
            self.db.insertPartialEmoji(emoji.id,emoji.name,int(emoji.animated),data)
        else:
            # Add Guild
            if(not self.db.guildExists(emoji.guild_id)):
                await self.addGuild(emoji.guild)
            # Add emoji
            if(not self.db.emojiExists(emoji.id)):
                self.db.insertEmoji(emoji.id,emoji.guild_id,emoji.name,int(emoji.animated),sqlite3.Binary(await emoji.url.read()))

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
        if(not self.db.emojiExists(reaction.emoji.id)):
            await self.addEmoji(reaction.emoji)
        async for user in reaction.users():
            # Add User
            if(not self.db.userExists(user.id)):
                await self.addUser(user)
            # Add Reaction - note, the if is needed because of how reactions are stored
            if(not self.db.reactionExists(reaction.emoji.id,user.id,reaction.message.id)):
                self.db.insertReaction(reaction.emoji.id,user.id,reaction.message.id)

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
        if(not self.db.emojiExists(raw_reaction.emoji.id) and self.db.messageExists(raw_reaction.message_id)):
            await self.addEmoji(raw_reaction.emoji)
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


