import sqlite3

class DiscordDB:

    def __init__(self, path):
        self.db = sqlite3.connect(path)
        self.cursor = self.db.cursor()

        self.cursor.execute('''
CREATE TABLE IF NOT EXISTS "guild" (
	"guild_id"	INTEGER,
	"name"	TEXT,
	"file_id"	INTEGER,
	FOREIGN KEY("file_id") REFERENCES "file",
	PRIMARY KEY("guild_id")
)''')
        self.cursor.execute('''
CREATE TABLE IF NOT EXISTS "guild_property" (
	"guild_id"	INTEGER,
	"property"	TEXT,
	"value"	TEXT,
	FOREIGN KEY("guild_id") REFERENCES "guild",
	PRIMARY KEY("guild_id","property")
)''')
        self.cursor.execute('''
CREATE TABLE IF NOT EXISTS "user" (
	"user_id"	INTEGER,
	"username"	TEXT,
	"discriminator"	INTEGER,
	"is_bot"	INTEGER,
	"file_id"	INTEGER,
	PRIMARY KEY("user_id"),
	FOREIGN KEY("file_id") REFERENCES "file"
)''')
        self.cursor.execute('''
CREATE TABLE IF NOT EXISTS "text_channel" (
    "channel_id"	INTEGER,
    "guild_id"	INTEGER,
    "name"	TEXT,
    "last_message"	TEXT,
    FOREIGN KEY("guild_id") REFERENCES "guild",
    PRIMARY KEY("channel_id")
)''')
        self.cursor.execute('''
CREATE TABLE IF NOT EXISTS "dm_message" (
    "message_id"	INTEGER,
    "user_id"	INTEGER,
    "content"	TEXT,
    "sent"	TEXT,
    "was_deleted"	INTEGER,
    "has_file"	INTEGER,
    FOREIGN KEY("user_id") REFERENCES "user",
    PRIMARY KEY("message_id")
)''')
        self.cursor.execute('''
CREATE TABLE IF NOT EXISTS "message" (
    "message_id"	INTEGER,
    "guild_id"	INTEGER,
    "channel_id"	INTEGER,
    "user_id"	INTEGER,
    "type"	TEXT,
    "content"	TEXT,
    "sent"	TEXT,
    "was_deleted"	INTEGER,
    "has_file"	INTEGER,
    FOREIGN KEY("guild_id") REFERENCES "guild",
    FOREIGN KEY("channel_id") REFERENCES "text_channel",
    FOREIGN KEY("user_id") REFERENCES "user",
    PRIMARY KEY("message_id")
)''')
        self.cursor.execute('''
CREATE TABLE IF NOT EXISTS "emoji" (
	"emoji_id"	INTEGER,
	"guild_id"	INTEGER,
	"file_id"	INTEGER,
	"name"	TEXT,
	"is_animated"	INTEGER,
	FOREIGN KEY("file_id") REFERENCES "file",
	PRIMARY KEY("emoji_id"),
	FOREIGN KEY("guild_id") REFERENCES "guild"
)''')
        self.cursor.execute('''
CREATE TABLE IF NOT EXISTS "warning" (
    "user_id"	INTEGER,
    "guild_id"	INTEGER,
    "datetime"	TEXT,
    "reason"	TEXT,
    FOREIGN KEY("user_id") REFERENCES "user",
    FOREIGN KEY("guild_id") REFERENCES "guild",
    PRIMARY KEY("user_id","guild_id","datetime")
)''')

        self.cursor.execute('''
CREATE TABLE IF NOT EXISTS "member" (
	"user_id"	INTEGER,
	"guild_id"	INTEGER,
	"nickname"	TEXT,
	"last_warning"	TEXT,
	"last_message"	TEXT,
	"has_left"	INTEGER,
	FOREIGN KEY("guild_id") REFERENCES "guild",
	FOREIGN KEY("user_id") REFERENCES "user",
	PRIMARY KEY("user_id","guild_id")
)''')
        self.cursor.execute('''
CREATE TABLE IF NOT EXISTS "reaction" (
    "emoji_id"	INTEGER,
    "user_id"	INTEGER,
    "message_id"	INTEGER,
    FOREIGN KEY("user_id") REFERENCES "user",
    FOREIGN KEY("emoji_id") REFERENCES "emoji",
    PRIMARY KEY("emoji_id","user_id","message_id")
)''')
        self.cursor.execute('''
CREATE TABLE IF NOT EXISTS "file" (
	"file_id"	INTEGER,
	"type"	TEXT,
	"reference_id"	INTEGER,
	"file_name"	TEXT,
	"file_type"	TEXT,
	"data"	BLOB,
	PRIMARY KEY("file_id")
)''')

    def start(self):
        self.cursor.execute("BEGIN")

    def commit(self):
        self.db.commit()

    def guildExists(self,guild_id):
        return len(self.cursor.execute('''SELECT guild_id FROM guild WHERE guild_id = ?''',
                                       (guild_id,)).fetchall()) > 0
    def channelExists(self,channel_id):
        return len(self.cursor.execute('''SELECT channel_id FROM text_channel WHERE channel_id = ?''',
                                       (channel_id,)).fetchall()) > 0
    def userExists(self,user_id):
        return len(self.cursor.execute('''SELECT user_id FROM user WHERE user_id = ?''',
                                       (user_id,)).fetchall()) > 0
    def memberExists(self,user_id,guild_id):
        return len(self.cursor.execute('''SELECT user_id FROM member WHERE user_id = ? AND guild_id = ?''',
                                       (user_id,guild_id,)).fetchall()) > 0
    def emojiExists(self,emoji_id):
        return len(self.cursor.execute('''SELECT emoji_id FROM emoji WHERE emoji_id = ?''',
                                       (emoji_id,)).fetchall()) > 0
    def messageExists(self,message_id):
        return len(self.cursor.execute('''SELECT message_id FROM message WHERE message_id = ?''',
                                       (message_id,)).fetchall()) > 0
    def dmMessageExists(self,message_id):
        return len(self.cursor.execute('''SELECT message_id FROM dm_message WHERE message_id = ?''',
                                       (message_id,)).fetchall()) > 0
    def reactionExists(self,emoji_id,user_id,message_id):
        return len(self.cursor.execute('''SELECT emoji_id FROM reaction WHERE emoji_id = ? AND user_id = ? AND message_id = ?''',
                                       (emoji_id,user_id,message_id,)).fetchall()) > 0
    def fileExists(self,type,reference_id,data):
        return len(self.cursor.execute('''SELECT file_id FROM file WHERE type = ? AND reference_id = ? AND data = ?''',
                                       (type,reference_id,data,)).fetchall()) > 0
    def propertyExists(self,guild_id,property):
        return len(self.cursor.execute('''SELECT value FROM guild_property WHERE guild_id = ? AND property = ?''',
                                       (guild_id,property)).fetchall()) > 0



    def insertDMMessage(self,message_id,user_id,content,sent,has_file):
        self.cursor.execute('''INSERT INTO dm_message(message_id,user_id,content,sent,was_deleted,has_file) VALUES(?,?,?,?,0,?)''',
                            (message_id,user_id,content,sent,has_file))
    def insertEmoji(self,emoji_id,guild_id,name,is_animated,file_id):
        self.cursor.execute('''INSERT INTO emoji(emoji_id,guild_id,name,is_animated,file_id) VALUES(?,?,?,?,?)''',
                            (emoji_id,guild_id,name,is_animated,file_id))
    def insertPartialEmoji(self,emoji_id,name,is_animated,file_id):
        self.cursor.execute('''INSERT INTO emoji(emoji_id,name,is_animated,file_id) VALUES(?,?,?,?)''',
                            (emoji_id,name,is_animated,file_id))
    def insertUnicodeEmoji(self,emoji_id,name):
        self.cursor.execute('''INSERT INTO emoji(emoji_id,name,is_animated) VALUES(?,?,0)''',
                            (emoji_id,name))
    def insertGuild(self,guild_id,name,file_id):
        self.cursor.execute('''INSERT INTO guild(guild_id,name,file_id) VALUES(?,?,?)''',
                            (guild_id,name,file_id))
    def insertMember(self,user_id,guild_id,nickname,has_left):
        self.cursor.execute('''INSERT INTO member(user_id,guild_id,nickname,last_warning,last_message,has_left) VALUES(?,?,?,null,null,?)''',
                            (user_id,guild_id,nickname,has_left))
    def insertMessage(self,message_id,guild_id,channel_id,user_id,type,content,sent,has_file):
        self.cursor.execute('''INSERT INTO message(message_id,guild_id,channel_id,user_id,type,content,sent,was_deleted,has_file) VALUES(?,?,?,?,?,?,?,0,?)''',
                            (message_id,guild_id,channel_id,user_id,type,content,sent,has_file))
    def insertReaction(self,emoji_id,user_id,message_id):
        self.cursor.execute('''INSERT INTO reaction(emoji_id,user_id,message_id) VALUES(?,?,?)''',
                            (emoji_id,user_id,message_id))
    def insertTextChannel(self,channel_id,guild_id,name):
        self.cursor.execute('''INSERT INTO text_channel(channel_id,guild_id,name,last_message) VALUES(?,?,?,null)''',
                            (channel_id,guild_id,name))
    def insertUser(self,user_id,username,discriminator,is_bot,file_id):
        self.cursor.execute('''INSERT INTO user(user_id,username,discriminator,is_bot,file_id) VALUES(?,?,?,?,?)''',
                            (user_id,username,discriminator,is_bot,file_id))
    def insertWarning(self,user_id,guild_id,datetime,reason):
        self.cursor.execute('''INSERT INTO warning(user_id,guild_id,datetime,reason) VALUES(?,?,?,?)''',
                            (user_id,guild_id,datetime,reason))
    def insertFile(self,file_id,type,reference_id,file_name,file_type,data):
        self.cursor.execute('''INSERT INTO file(file_id,type,reference_id,file_name,file_type,data) VALUES(?,?,?,?,?,?)''',
                            (file_id,type,reference_id,file_name,file_type,data))



    def select(self,query):
        return self.cursor.execute(query).fetchall()


    def getMaxFileID(self):
        value = self.cursor.execute('''SELECT MAX(file_id) FROM file''').fetchall()
        return value[0][0] if value[0][0] != None else 0
    def getNumOfWarningsForMember(self,user_id,guild_id):
        value = self.cursor.execute('''SELECT COUNT(datetime) FROM warning WHERE user_id = ? AND guild_id = ?''',
                                    (user_id,guild_id)).fetchall()
        return value[0][0] if value[0][0] != None else 0
    def getGuildPropertyValue(self,guild_id,property):
        value = self.cursor.execute('''SELECT value FROM guild_property WHERE guild_id = ? AND property = ?''',
                                    (guild_id,property)).fetchall()
        try:
            return int(value[0][0])
        except TypeError:
            return value[0][0]



    def updateChannelLastMessage(self,channel_id,message_time):
        self.db.execute('''UPDATE text_channel SET last_message = ? WHERE channel_id = ?''',
                        (message_time,channel_id))
    def updateMemberLastMessage(self,user_id,guild_id,message_time):
        self.db.execute('''UPDATE member SET last_message = ? WHERE user_id = ? AND guild_id = ?''',
                        (message_time,user_id,guild_id))
    def updateMemberLastWarning(self,user_id,guild_id,message_time):
        self.db.execute(''''UPDATE member SET last_warning = ? WHERE user_id = ? AND guild_id = ?''',
                        (message_time,user_id,guild_id))
    def updateGuildProperty(self,guild_id,property,value):
        self.db.execute('''UPDATE guild_property SET value = ? WHERE guild_id = ? AND property = ?''',
                        (value,guild_id,property))
    def updateMemberIsInGuild(self,user_id,guild_id,has_left):
        self.db.execute('''UPDATE member SET has_left = ? WHERE user_id = ? AND guild_id = ?''',
                        (has_left,user_id,guild_id))


    def addDefaultGuildProperties(self,channel_id):
        self.db.execute('''INSERT INTO guild_property(guild_id,property,value) VALUES(?,"commands_channel",null)''',
                        (channel_id,))
        self.db.execute('''INSERT INTO guild_property(guild_id,property,value) VALUES(?,"mod_commands_channel",null)''',
                        (channel_id,))
        self.db.execute('''INSERT INTO guild_property(guild_id,property,value) VALUES(?,"announcement_channel",null)''',
                        (channel_id,))
        self.db.execute('''INSERT INTO guild_property(guild_id,property,value) VALUES(?,"kick_warning_num",3)''',
                        (channel_id,))
        self.db.execute('''INSERT INTO guild_property(guild_id,property,value) VALUES(?,"ban_warning_num",5)''',
                        (channel_id,))
        self.db.execute('''INSERT INTO guild_property(guild_id,property,value) VALUES(?,"warning_reset_days",30)''',
                        (channel_id,))
        self.db.execute('''INSERT INTO guild_property(guild_id,property,value) VALUES(?,"banned_words",null)''',
                        (channel_id,))
        self.db.execute('''INSERT INTO guild_property(guild_id,property,value) VALUES(?,"timezone",null)''',
                        (channel_id,))
