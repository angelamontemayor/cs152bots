# bot.py
import discord
from discord.ext import commands
import os
import json
import logging
import re
import requests
from report import Report
from review import Review
import pdb

# Set up logging to the console
logger = logging.getLogger('discord')
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

# There should be a file called 'tokens.json' inside the same folder as this file
token_path = 'tokens.json'
if not os.path.isfile(token_path):
    raise Exception(f"{token_path} not found!")
with open(token_path) as f:
    # If you get an error here, it means your token is formatted incorrectly. Did you put it in quotes?
    tokens = json.load(f)
    discord_token = tokens['discord']


class ModBot(discord.Client):
    def __init__(self): 
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix='.', intents=intents)
        self.group_num = None
        self.mod_channels = {} # Map from guild to the mod channel id for that guild
        self.reports = {} # Map from user IDs to the state of their report
        self.reports_list = {} # Map from Report Number to (userID, timeStamp, reportedMessadeLink, containsChild)
        self.report_num = 0 # Counter for report number
        self.reviews = {} # Map from mod IDs to the state of their reviews
        self.users_with_strike = set() # Contains user IDs who have already received warnings
        self.mod_channel = None # Set to group 25 Mod Channel

    async def on_ready(self):
        print(f'{self.user.name} has connected to Discord! It is these guilds:')
        for guild in self.guilds:
            print(f' - {guild.name}')
        print('Press Ctrl-C to quit.')

        # Parse the group number out of the bot's name
        match = re.search('[gG]roup (\d+) [bB]ot', self.user.name)
        if match:
            self.group_num = match.group(1)
        else:
            raise Exception("Group number not found in bot's name. Name format should be \"Group # Bot\".")

        # Find the mod channel in each guild that this bot should report to
        for guild in self.guilds:
            for channel in guild.text_channels:
                if channel.name == f'group-{self.group_num}-mod':
                    self.mod_channels[guild.id] = channel
                    self.mod_channel = channel
        

    async def on_message(self, message):
        '''
        This function is called whenever a message is sent in a channel that the bot can see (including DMs). 
        Currently the bot is configured to only handle messages that are sent over DMs or in your group's "group-#" channel. 
        '''
        # Ignore messages from the bot 
        if message.author.id == self.user.id:
            return

        # Check if this message was sent in a server ("guild") or if it's a DM
        if message.guild:
            await self.handle_channel_message(message)
        else:
            await self.handle_dm(message)


    async def handle_dm(self, message):
        # Handle a help message
        if message.content == Report.HELP_KEYWORD:
            reply =  "Use the `report` command to begin the reporting process.\n"
            reply += "Use the `cancel` command to cancel the report process.\n"
            await message.channel.send(reply)
            return

        author_id = message.author.id
        responses = []

        # Only respond to messages if they're part of a reporting flow
        if author_id not in self.reports and not message.content.startswith(Report.START_KEYWORD):
            return

        # If we don't currently have an active report for this user, add one
        if author_id not in self.reports:
            self.reports[author_id] = Report(self)

        # Let the report class handle this message; forward all the messages it returns to uss
        responses = await self.reports[author_id].handle_message(message)
        for r in responses:
            await message.channel.send(r)

        # If the report is complete or cancelled
        if self.reports[author_id].report_canceled() or self.reports[author_id].report_complete():
            # If report completed, update reports_list map and send report to mod channel
            if self.reports[author_id].report_complete():
                self.report_num += 1
                time_stamp = str(self.reports[author_id].get_time())
                reported_link = str(self.reports[author_id].get_link())
                containsChild = self.reports[author_id].image_contains_child()
                self.reports_list[self.report_num] = (author_id, time_stamp, reported_link, containsChild)
                reply = 'New report has been filed:\n'
                reply += 'Case #' + str(self.report_num) + '\nReported by UserID: ' + str(author_id) + '\nTime Filed: ' + time_stamp + '\nReported Image Link: ' + reported_link + '\n'
                if containsChild:
                    reply += 'Image believed to contain a child.\n'
                else:
                    reply += 'Image is not believed to contain a child.\n'
                self.mod_channel.send(reply)
            self.reports.pop(author_id)
            return

    async def handle_channel_message(self, message):
        mod_channel = self.mod_channels[message.guild.id]
        author_id = message.author.id
        # handle messages sent in the "group-#" channel
        if message.channel.name == f'group-{self.group_num}':
            if message.content == Report.HELP_KEYWORD:
                reply =  "Use the `report` command to begin the reporting process.\n"
                reply += "Use the `cancel` command to cancel the report process.\n"
                await message.channel.send(reply)
                return
            
            responses = []

            # Only respond to messages if they're part of a reporting flow
            if author_id not in self.reports and not message.content.startswith(Report.START_KEYWORD):
                return

            # If we don't currently have an active report for this user, add one
            if author_id not in self.reports:
                self.reports[author_id] = Report(self)

            # Let the report class handle the rest of the flow
            responses = await self.reports[author_id].handle_message(message)
            for r in responses:
                await message.channel.send(r)

            # If report completed, update reports_list map and send report to mod channel
            if self.reports[author_id].report_canceled() or self.reports[author_id].report_complete():
                if self.reports[author_id].report_complete():
                    self.report_num += 1
                    time_stamp = str(self.reports[author_id].get_time())
                    reported_link = str(self.reports[author_id].get_link())
                    containsChild = self.reports[author_id].image_contains_child()
                    self.reports_list[self.report_num] = (author_id, time_stamp, reported_link, containsChild)
                    reply = 'New report has been filed:\n'
                    reply += 'Case #' + str(self.report_num) + '\nReported by UserID: ' + str(author_id) + '\nTime Filed: ' + time_stamp + '\nReported Image Link: ' + reported_link + '\n'
                    if containsChild:
                        reply += 'Image believed to contain a child.\n'
                    else:
                        reply += 'Image is not believed to contain a child.\n'
                    await mod_channel.send(reply)
                self.reports.pop(author_id)
                return
        
        # handle messages sent in the mod channel
        elif message.channel.name == f'group-{self.group_num}-mod':
            if message.content == Review.HELP_KEYWORD:
                reply =  "Use the `review` command to begin the reviewing process.\n"
                reply += "Use the `cancel` command to cancel the reviewing process.\n"
                reply += "Use the `list` command to view all unreviewed reports.\n"
                await message.channel.send(reply)
                return
        
            # list all unreviewed reports
            if message.content == Review.LIST_KEYWORD:
                reply = "Unreviewed reports:\n\n"
                for key in self.reports_list.keys():
                    userID, time_stamp, reported_link, containsChild = self.reports_list[key] 
                    reply += 'Case #' + str(key) + '\nReported by UserID: ' + str(userID) + '\nTime Filed: ' + time_stamp + '\nReported Image Link: ' + reported_link + '\n'
                    if containsChild:
                        reply += 'Image believed to contain a child.'
                    else:
                        reply += 'Image is not believed to contain a child.'
                await message.channel.send(reply)
                return
            
            # Only respond to messages if they're part of a review flow
            if author_id not in self.reviews and not message.content.startswith(Review.START_KEYWORD):
                return
           
           # If we don't currently have an active review for this mod, add one
            if author_id not in self.reviews:
                self.reviews[author_id] = Review(self, self.reports_list)
            
            # Let the review class handle the rest of the flow
            responses = await self.reviews[author_id].handle_message(message)
            for r in responses:
                await mod_channel.send(r)

            # if we are at the end of the review flow
            if self.reviews[author_id].case_closed():
                # Implement consequences on abuser has indeed violated guidelines
                if self.reviews[author_id].is_violation():
                    # find the ID of the abuser
                    link = self.reviews[author_id].get_link()
                    m = re.search('/(\d+)/(\d+)/(\d+)', link)
                    channel = message.guild.get_channel(int(m.group(2)))
                    m = await channel.fetch_message(int(m.group(3)))
                    abuserID = m.author
                    
                    # delete the reported message
                    await m.delete()
                    
                    # check past violation history
                    if abuserID in self.users_with_strike:
                        await abuserID.send("Your account has been banned due to activity that violated our guidelines. If you would like to appeal this decision, email hr@group25.com.")
                        reply = "The reported user (" + str(abuserID) + ") has violated community guidelines in the past. System has removed the account from the platform according to our strike policy."
                        await mod_channel.send(reply)
                    else:
                        self.users_with_strike.add(abuserID)
                        await abuserID.send("You have received a warning for a post that violated our community guidelines. If you violate the guidelines again, your account will be permanently banned.")
                        reply = "The reported user (" + str(abuserID) + ") has not violated community guidelines in the past. System has added a strike to the user's account."
                        await mod_channel.send(reply)
                if not self.reviews[author_id].is_canceled_review():
                    self.reports_list.pop(self.reviews[author_id].get_report_num())
                self.reviews.pop(author_id)
        else:
            return
        
    
    def eval_text(self, message):
        ''''
        TODO: Once you know how you want to evaluate messages in your channel, 
        insert your code here! This will primarily be used in Milestone 3. 
        '''
        
        return message

     
    def code_format(self, text):
        ''''
        TODO: Once you know how you want to show that a message has been 
        evaluated, insert your code here for formatting the string to be 
        shown in the mod channel. 
        '''
        return ""


client = ModBot()
client.run(discord_token)