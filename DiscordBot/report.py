from enum import Enum, auto
import discord
import re

class State(Enum):
    REPORT_START = auto()
    AWAITING_MESSAGE = auto()
    MESSAGE_IDENTIFIED = auto()
    REPORT_COMPLETE = auto()
    AWAITING_COMPLAINT = auto()
    CONFIRMING_CSAM = auto()
    REPORT_CANCELED = auto()

class Report:
    START_KEYWORD = "report"
    CANCEL_KEYWORD = "cancel"
    HELP_KEYWORD = "help"

    def __init__(self, client):
        self.state = State.REPORT_START
        self.client = client
        self.message = None
        self.reported_message_link = None
        self.reported_time = None
        self.contains_child = False
        
    async def handle_message(self, message):
        '''
        This function makes up the meat of the user-side reporting flow. It defines how we transition between states and what 
        prompts to offer at each of those states. You're welcome to change anything you want; this skeleton is just here to
        get you started and give you a model for working with Discord. 
        '''
        if message.content == self.CANCEL_KEYWORD:
            self.state = State.REPORT_CANCELED
            return ["Report cancelled."]
        
        if self.state == State.REPORT_START:
            reply =  "Thank you for starting the reporting process. "
            reply += "Say `help` at any time for more information.\n\n"
            reply += "Please copy paste the link to the message you want to report.\n"
            reply += "You can obtain this link by right-clicking the message and clicking `Copy Message Link`."
            self.state = State.AWAITING_MESSAGE
            self.reported_time = message.created_at
            return [reply]
        
        if self.state == State.AWAITING_MESSAGE:
            # Parse out the three ID strings from the message link
            raw = message.content
            m = re.search('/(\d+)/(\d+)/(\d+)', message.content)
            if not m:
                return ["I'm sorry, I couldn't read that link. Please try again or say `cancel` to cancel."]
            guild = self.client.get_guild(int(m.group(1)))
            if not guild:
                return ["I cannot accept reports of messages from guilds that I'm not in. Please have the guild owner add me to the guild and try again."]
            channel = guild.get_channel(int(m.group(2)))
            if not channel:
                return ["It seems this channel was deleted or never existed. Please try again or say `cancel` to cancel."]
            try:
                message = await channel.fetch_message(int(m.group(3)))
                self.reported_message_link = raw
            except discord.errors.NotFound:
                return ["It seems this message was deleted or never existed. Please try again or say `cancel` to cancel."]

            # Here we've found the message - it's up to you to decide what to do next!
            self.state = State.MESSAGE_IDENTIFIED
            #return ["I found this message:", "```" + message.author.name + ": " + message.content + "```", \
            #      "This is all I know how to do right now - it's up to you to build out the rest of my reporting flow!"]
        
        if self.state == State.AWAITING_COMPLAINT:
            m = message.content
            if m == '1' or m == '2' or m == '3' or m == '5' or m == '6' or m == '7' or m == '8':
                self.state = State.REPORT_COMPLETE
                return ["Thank you for your report. We appreciate your feedback."]
            elif m == '4':
                self.state = State.CONFIRMING_CSAM
                return ["Does this image contain a child? Y/N"]
            else:
                return ["Sorry, I don't quite understand your reply. Please enter a number 1-8 corresponding to your reason for reporting: \n`1` for Hate Speech\n`2` for Spam\n`3` for Scam or Fraud\n`4` for Nudity or Sexual Activity\n`5` for Bullying or Harassment\n`6` for Illegal Activity\n`7` for Violence\n or, `8` I just don't like it."]

        if self.state == State.CONFIRMING_CSAM:
            m = message.content.strip().lower()
            if m == 'y' or m == 'n' or m == 'yes' or m == 'no':
                if m == 'y' or m == 'n':
                    self.contains_child = True
                self.state = State.REPORT_COMPLETE # move this later once you implement the options below
                return ["Thank you for your report. We appreciate your feedback. How would you like to proceed?\n`1` Block user\n`2` Unfollow user\n`3`Learn more about our community guidelines"]

        if self.state == State.MESSAGE_IDENTIFIED:
            #return ["<insert rest of reporting flow here>"]
            # insert rest of reporting flow here
            self.state = State.AWAITING_COMPLAINT
            reply =  "Thank you for sharing the message. "
            reply += "Why are you reporting this image? Please reply with:\n`1` for Hate Speech\n`2` for Spam\n`3` for Scam or Fraud\n`4` for Nudity or Sexual Activity\n`5` for Bullying or Harassment\n`6` for Illegal Activity\n`7` for Violence\n or, `8` I just don't like it."
            return [reply]

        return []

    def report_complete(self):
        return self.state == State.REPORT_COMPLETE
    
    def report_canceled(self):
        return self.state == State.REPORT_CANCELED
    
    def get_link(self):
        return self.reported_message_link

    def get_time(self):
        return self.reported_time
    
    def image_contains_child(self):
        return self.contains_child


    

    


    

