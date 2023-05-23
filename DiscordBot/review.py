from enum import Enum, auto
import discord
import re

class State(Enum):
    REVIEW_START = auto()
    REVIEW_CANCLED = auto()
    AWAITING_REPORT_NUM = auto()
    REVIEW_COMPLETE = auto()
    CONFIRMING_HASH = auto()
    CONFIRMING_CSAM = auto()
    FURTHER_REVIEW = auto()

class Review:
    START_KEYWORD = "review"
    LIST_KEYWORD = 'list'
    CANCEL_KEYWORD = "cancel"
    HELP_KEYWORD = "help"

    def __init__(self, client, reports_list):
        self.state = State.REVIEW_START
        self.client = client
        self.curr_report_num = None
        self.reports_list = reports_list
        self.link = None 
        
    async def handle_message(self, message):

        if message.content == self.CANCEL_KEYWORD:
            self.state = State.REVIEW_CANCLED
            return ["Review cancelled."]
        
        if self.state == State.REVIEW_START:
            reply = "Please enter a report number:"
            self.state = State.AWAITING_REPORT_NUM
            return [reply]
        
        if self.state == State.AWAITING_REPORT_NUM:
            m = message.content
            if int(m) not in self.reports_list:
                return ["Sorry, that is not a valid report case number. Use the `list` command to view all unreviewed reports."]
            else:
                # print report details
                self.state = State.CONFIRMING_HASH
                self.curr_report_num = int(m)
                self.link = self.reports_list[self.curr_report_num][2]
                return ["Please hash check the reported image with the NCMEC database. Is the reported image already in the database? Y/N"]
        
        if self.state == State.CONFIRMING_HASH:
            m = message.content.strip().lower()
            if m == 'y' or m == 'yes':
                self.state = State.REVIEW_COMPLETE 
                return ["The image has been removed from the platform and sent to NCMEC in accordance to our guidelines. Thank you for reviewing this report."]
            elif m == 'n' or m =='no':
                self.state = State.CONFIRMING_CSAM
                reply = "Open " + self.link + " to view the reported image. Does the image contain child sexual abuse material? Y/N"
                return [reply]
            else:
                return ["Sorry, I don't quite understand your reply. Please enter `Y` if the reported image is already in the NCMEC database, and `N` otherwise."]
        
        if self.state == State.CONFIRMING_CSAM:
            m = message.content.strip().lower()
            if m == 'y' or m == 'yes':
                self.state = State.REVIEW_COMPLETE 
                return ["The image has been removed from the platform and sent to NCMEC in accordance to our guidelines. Thank you for reviewing this report."]
            elif m == 'n' or m =='no':
                self.state = State.FURTHER_REVIEW
                return ["The reported image does not contain CSAM. The material will require further review."]
            else:
                return ["Sorry, I don't quite understand your reply. Please enter `Y` if the reported image contains child sexual abuse material, and `N` otherwise."]
            
        return []

    def case_closed(self):
        return self.state == State.REVIEW_COMPLETE or self.state == State.FURTHER_REVIEW or self.state == State.REVIEW_CANCLED
    
    def is_canceled_review(self):
        return self.state == State.REVIEW_CANCLED
    
    def is_violation(self):
        return self.state == State.REVIEW_COMPLETE 
    
    def get_link(self):
        return self.link
    
    def get_report_num(self):
        return self.curr_report_num
    

    
