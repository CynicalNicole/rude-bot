import discord
from discord.ext import commands
import logging
import asyncio
import json
import sqlite3
import os
import random

#Set up logging
logger = logging.getLogger('discord')
logger.setLevel(logging.WARNING)
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

#Load config from config.json
class config:
    def __init__(self):
        #Dictionart
        self.configDict = self.loadConfig("data/config.json")

        #Four Vars
        self.owner = self.configDict['bot-owner']
        self.admins = self.configDict['admins']
        self.validChannels = self.configDict['whitelisted-channels']   
        self.botToken = self.configDict['bot-token']
        self.maxRoll = self.configDict['max-roll']
        self.chatMessages = self.configDict['chat-messages']
        #I can count

    #Load dict from file
    def loadConfig(self, configFile):
        with open(configFile) as json_file:
            return json.load(json_file)
        #json_file = open(configFile)
        #json_string = json_file.read()
        

    #Assign all
    def assignConfig(self):
        self.owner = self.configDict['bot-owner']
        self.admins = self.configDict['admins']   
        self.validChannels = self.configDict['whitelisted-channels']
        self.botToken = self.configDict['bot-token']
        self.maxRoll = self.configDict['max-roll']
        self.chatMessages = self.configDict['chat-messages']

    #Method for reloading the config
    def reloadConfig(self):
        self.configDict = self.loadConfig("data/config.json")
        self.assignConfig()

    def editConfig(self, admins=None, cmdCh=None, rollChange=None, messageChange=None):
        if (admins != None):
            self.configDict['admins'] = admins

        if (cmdCh != None):
            self.configDict['whitelisted-channels'] = cmdCh

        if (rollChange != None):
            self.configDict['max-roll'] = int(rollChange)

        if (messageChange != None):
            self.configDict['chat-messages'] = messageChange

        self.saveConfig()
        self.reloadConfig()
        
    def saveConfig(self):
        with open('data/config.json', 'w') as outfile:
            json.dump(self.configDict, outfile, indent=4, ensure_ascii=False)

    def addMessage(self, newMessage : str):
        curMessages = self.chatMessages
        curMessages.append(newMessage)

        self.editConfig(messageChange=curMessages)
        return len(curMessages) - 1

    def addChannel(self, channel):
        curChannels = self.validChannels
        curChannels.append(int(channel.id))

        self.editConfig(cmdCh=curChannels)

    def removeChannel(self, channelId=None, channelPos=None):
        curChannels = self.validChannels

        if channelId != None:
            try:
                curChannels.remove(channelId)
                self.editConfig(cmdCh=curChannels)
                return 0
            except ValueError:
                return 1

        if channelPos != None:
            try:
                curChannels.remove(curChannels[channelPos])
                self.editConfig(cmdCh=curChannels)
                return 0
            except IndexError:
                return 2
            except ValueError:
                return 1

        return -1

    def removeMessage(self, messagePos=None):
        curMessages = self.chatMessages

        if messagePos != None:
            try:
                msgRemoved = curMessages[messagePos]
                curMessages.remove(msgRemoved)
                self.editConfig(messageChange=curMessages)
                return 0, msgRemoved
            except IndexError:
                return 2
            except ValueError:
                return 1

        return -1
                

#Create config
config = config()

#Create the bot client
client = commands.Bot(command_prefix='~')

#Custom Definitions
def is_owner(ctx):
    return int(ctx.message.author.id) == config.owner

def is_admin(ctx):
    return int(ctx.message.author.id) in config.admins

def correct_channel(ctx):
    return int(ctx.message.channel.id) in config.validChannels

def RepresentsInt(s):
    try: 
        int(s)
        return True
    except ValueError:
        return False

#Now we can setup the on-ready event
@client.event
async def on_ready():
    client.get_all_members()
    client.get_all_channels()

    print('Logged in...')
    print('------------')
    print('CONFIG:')
    print('Owner: ' + str(config.owner))
    print('Admins: ' + str(config.admins))
    print('Roll (1/x): ' + str(config.maxRoll))
    print('------------')
    print('Have a lovely day <3')
    print('------------')
    print('')

@client.command()
@commands.check(is_owner)
async def shutdown(ctx):
    client.close()
    exit()

@client.command()
@commands.check(is_owner)
async def setname(ctx, name : str):
    await client.user.edit(username=name)
    await ctx.channel.send("Updated name: " + name)

@client.command()
@commands.check(is_admin)
async def setroll(ctx, roll : str):
    if RepresentsInt(roll):
        config.editConfig(rollChange=roll)
        await ctx.channel.send("Updated max roll: " + str(roll))
        return
    
    await ctx.channel.send("The roll was not a valid integer.")

@client.command()
@commands.check(is_admin)
async def addmessage(ctx, msg : str):
    position = config.addMessage(msg)
    await ctx.channel.send("Added message [" + str(position) + "]: " + msg)

@client.command()
@commands.check(is_admin)
async def removemessage(ctx, msgPos : str):
    if RepresentsInt(msgPos):
        resp, removed = config.removeMessage(int(msgPos))
        if resp == 0:
            await ctx.channel.send("Removed message: " + removed)
            return

        if resp == 1 or resp == 2:
            await ctx.channel.send("Invalid message index.")
            return

        await ctx.channel.send("An unknown error has occurred.")
        return

    await ctx.channel.send("The index was not a valid integer.")

@client.command()
@commands.check(is_admin)
async def listmessages(ctx):
    pos = 0
    msglist = ''
    for msg in config.chatMessages: 
        msglist += "[" + str(pos) + "]: " + msg + "\n"
        pos += 1

    await ctx.channel.send(msglist)

@client.command()
@commands.check(is_admin)
async def addchannel(ctx, cname : str):
    if ctx.guild == None:
        return

    channel = discord.utils.get(ctx.guild.channels, name=cname)
    if channel == None:
        return

    config.addChannel(channel)
    await ctx.channel.send("Added channel to whitelist: " + channel.name)

@client.command()
@commands.check(is_admin)
async def removechannel(ctx, cname : str):
    if ctx.guild == None:
        return

    channel = discord.utils.get(ctx.guild.channels, name=cname)
    if channel == None:
        return

    resp = config.removeChannel(channelId=int(channel.id))

    if (resp == 0):
        await ctx.channel.send("Removed channel from whitelist: " + channel.name)
        return

    if (resp == 1):
        await ctx.channel.send("The specified channel does not exist in the whitelist.")
        return

    await ctx.channel.send("An unknown error has occurred.")

@client.command()
@commands.check(is_admin)
async def checkchannel(ctx):
    if ctx.guild == None:
        return
    
    if int(ctx.channel.id) in config.validChannels:
        await ctx.channel.send("This channel is whitelisted.")
    else:
        await ctx.channel.send("This channel is not whitelisted.")

@client.event
async def on_message(message):
    await client.wait_until_ready()
    if message.author.id == client.user.id:
        return

    channel = message.channel

    if channel.type == discord.ChannelType.private:
        return

    if message.content.startswith("~"):
        await client.process_commands(message)
    else:
        if int(channel.id) not in config.validChannels:
            return

        rngRoll = random.randint(1, config.maxRoll)
        if rngRoll == 1:
            msg = random.choice(config.chatMessages)
            msg = msg.format(usr=message.author.display_name)
            await channel.send(msg)

client.run(config.botToken)