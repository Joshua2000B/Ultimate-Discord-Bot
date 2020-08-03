import sqlite3

class DiscordDB:

    def __init__(self, path):
        self.db = sqlite3.connect(path)
        self.cursor = self.db.cursor()

        self.cursor.execute('''
CREATE TABLE IF NOT EXISTS "guild" (
    "guild_id"	INTEGER,
    "name"	TEXT,
    PRIMARY KEY("guild_id")
)''')
        self.cursor.execute('''
CREATE TABLE IF NOT EXISTS "user" (
    "user_id"	INTEGER,
    "username"	TEXT,
    "discriminator"	INTEGER,
    "is_bot"	INTEGER,
    "avatar"	BLOB,
    PRIMARY KEY("user_id")
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
	"name"	TEXT,
	"is_animated"	INTEGER,
	"file"	BLOB,
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
	PRIMARY KEY("user_id","guild_id"),
	FOREIGN KEY("user_id") REFERENCES "user",
	FOREIGN KEY("guild_id") REFERENCES "guild"
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


    def insertDMMessage(self,message_id,user_id,content,sent,has_file):
        self.cursor.execute('''INSERT INTO dm_message(message_id,user_id,content,sent,was_deleted,has_file) VALUES(?,?,?,?,0,?)''',
                            (message_id,user_id,content,sent,has_file))
    def insertEmoji(self,emoji_id,guild_id,name,is_animated,file):
        self.cursor.execute('''INSERT INTO emoji(emoji_id,guild_id,name,is_animated,file) VALUES(?,?,?,?,?)''',
                            (emoji_id,guild_id,name,is_animated,file))
    def insertPartialEmoji(self,emoji_id,name,is_animated,file):
        self.cursor.execute('''INSERT INTO emoji(emoji_id,name,is_animated,file) VALUES(?,?,?,?)''',
                            (emoji_id,name,is_animated,file))
    def insertGuild(self,guild_id,name):
        self.cursor.execute('''INSERT INTO guild(guild_id,name) VALUES(?,?)''',
                            (guild_id,name))
    def insertMember(self,user_id,guild_id,nickname):
        self.cursor.execute('''INSERT INTO member(user_id,guild_id,nickname,last_warning,last_message) VALUES(?,?,?,null,null)''',
                            (user_id,guild_id,nickname))
    def insertMessage(self,message_id,guild_id,channel_id,user_id,type,content,sent,has_file):
        self.cursor.execute('''INSERT INTO message(message_id,guild_id,channel_id,user_id,type,content,sent,was_deleted,has_file) VALUES(?,?,?,?,?,?,?,0,?)''',
                            (message_id,guild_id,channel_id,user_id,type,content,sent,has_file))
    def insertReaction(self,emoji_id,user_id,message_id):
        self.cursor.execute('''INSERT INTO reaction(emoji_id,user_id,message_id) VALUES(?,?,?)''',
                            (emoji_id,user_id,message_id))
    def insertTextChannel(self,channel_id,guild_id,name):
        self.cursor.execute('''INSERT INTO text_channel(channel_id,guild_id,name,last_message) VALUES(?,?,?,null)''',
                            (channel_id,guild_id,name))
    def insertUser(self,user_id,username,discriminator,is_bot,avatar):
        self.cursor.execute('''INSERT INTO user(user_id,username,discriminator,is_bot,avatar) VALUES(?,?,?,?,?)''',
                            (user_id,username,discriminator,is_bot,avatar))
    def insertWarning(self,user_id,guild_id,datetime,reason):
        self.cursor.execute('''INSERT INTO warning(user_id,guild_id,datetime,reason) VALUES(?,?,?,?)''',
                            (user_id,guild_id,datetime,reason))

    def select(self,query):
        return self.cursor.execute(query).fetchall()

    def updateChannelLastMessage(self,channel_id,message_time):
        self.db.execute('''UPDATE text_channel set last_message = ? WHERE channel_id = ?''',
                        (message_time,channel_id))
