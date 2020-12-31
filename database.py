import sqlite3

class db_connection:
    def __init__(self, dbpath):
        self.dbConnection = sqlite3.connect(dbpath, isolation_level=None)

        #First, we check the db
        self.dbStartup()

    def cleanup(self):
        self.dbConnection.close()

    def dbStartup(self):
        cursor = self.dbConnection.cursor()

        #Create GUILD table
        guild_create = """CREATE TABLE IF NOT EXISTS Guild 
        (Id INTEGER PRIMARY KEY UNIQUE,
        MaxRoll INTEGER)"""

        #Create MESSAGES table
        messages_create = """CREATE TABLE IF NOT EXISTS Messages 
        (Id INTEGER PRIMARY KEY AUTOINCREMENT, 
        GuildId INTEGER, 
        Message TEXT)"""

        #Create CHANNELS table
        channels_create = """CREATE TABLE IF NOT EXISTS Channels 
        (Id INTEGER PRIMARY KEY UNIQUE,
        GuildId INTEGER)"""

        cursor.executemany((guild_create, messages_create, channels_create))

    def getGuildInfo(self, guildId):
        cursor = self.dbConnection.cursor()
        query = """SELECT * FROM Guild WHERE Id = ?"""
        cursor.execute(query, (guildId,))

        #Fetch the first
        record = cursor.fetchone()

        if record == None:
            return None

        guild = guild_info(record['Id'], record['MaxRoll'])
        guild.setMessages(self.getMessagesForGuild(guild.Id))
        guild.setChannels(self.getChannelsForGuild(guild.Id))

        return guild

    def getMessagesForGuild(self, guildId):
        query = """SELECT Message FROM Messages WHERE GuildId = ?"""
        args = (guildId, )
        
        return self.fetchAllColumnAsList(query, args)

    def getChannelsForGuild(self, guildId):
        query = """SELECT Id FROM Channels WHERE GuildId = ?"""
        args = (guildId, )
        
        return self.fetchAllColumnAsList(query, args)

    def fetchAllColumnAsList(self, query, args):
        cursor = self.dbConnection.cursor()
        cursor.row_factory = lambda cursor, row: row[0]
        cursor.execute(query, args)

        return cursor.fetchall()

class guild_info:
    def __init__(self, Id, MaxRoll):
        self.Id = Id
        self.MaxRoll = MaxRoll
        self.Messages = []
        self.Channels = []

    def setMessages(self, messageList):
        self.Messages = messageList

    def setChannels(self, channelsList):
        self.Channels = channelsList

    