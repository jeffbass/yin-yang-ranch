"""chatbot.py: conversation classes, methods and attributes

Provides a simple conversation ability so the Librarian can answer simple
questions about motion detection, light detection, temperatures and other
information that is sent by imagenodes to imagehubs.

Copyright (c) 2018 by Jeff Bass.
License: MIT, see LICENSE for more details.
"""

import re
import sys
import pprint
import logging
import threading
from time import sleep
from datetime import datetime
from collections import deque
from ..data_tools import HubData

class Conversation:
    """ Methods and attributes that track conversations by (channel, person)
    """
    pass

class ChatBot:
    """ Methods and attributes to handle conversations

    Parses queries for intents and matches them up with things librarian has
    data about. Composes replies using data from imagehubs and facts
    derived from imagehubs (which in turn gather all their data from
    imagenodes). Uses simple keyword parsing for current testing. Every
    imagenode location is linked to keywords with if statements for now.

    Parameters:
        imagehubs (dict): dictionary of all known imagehubs
        memories (dict): pandas data series, one per imagedode per data type

    """
    def __init__(self, data=None):
        self.data = data

    def respond_to(self, request_str):
        """ Composes and returns a response to a request.

        If the request_str has multiple parts, splits them and processes request
        part. Puts the multiple parts back together before returning reply.
        A request_str has multiple parts for Gmail to include threadId, etc.
        A CLI request only has a text part.

        Parses request intents and composes reply by calling other methods.

        Parameters:
           request_str (str): the incoming request

        Returns:
           reply (str): the composed response to the request

        """
        separator = "|"
        split_request = separator in request_str
        if split_request:  # split into text and (all the rest) parts
            two_parts = request_str.split(separator, 1)
            request = two_parts[0]
            other_data = two_parts[1]
        else:  # just a simple text string; no separator
            request = request_str
        reply = ''
        # reply = '...your request was: ' + request
        # reply = reply + '\nIntents & concepts:'
        intents = self.parse_intents(request) # map request words to intent words
        """for intent_word, request_words in intents.items():
            reply = reply + '\n    ' + intent_word + ': '
            reply = reply + ', '.join(request_words)
        reply = reply + '\n'
        '\n'.join(reply, ) """
        compound_sentence = self.compose_reply(intents)
        reply_text = '\n'.join([reply, compound_sentence])
        if split_request:
            reply = separator.join([reply_text, other_data])
        else:
            reply = reply_text
        return reply

    def compose_reply(self, intents):
        """ Builds reply sentences by comparing intents to known factoids

        This function maps the specific information that has been requested to
        the information that is gathered by the imagenodes. It is a simple
        "hard wired" set of if statements (with comments to clarify a bit).

        Imagenodes have names that reflect their location; if there are matching
        location words in the intents, then a reply is composed about using
        fetched information (e.g. temperature or motion from barn imagenode).

        Water is a special case rather than a location. It will always get its
        own sentence added to the composed_reply.

        For testing, there is a limited set of functions implemented here. These
        can report current water state and current temperature state by
        location.

        TODO: add functions to answer questions about motion as well as
        temperature.

        TODO: add functions to answer questions about history as well as
        current status. (e.g., what was the low temperature behind the barn
        last night, in addition to what is the current temperature behind the
        barn.)

        Parameters:
            intents (dict): dictionary of intents created by parse_intent()
        Returns:
            compound_sentence (str): reply sentence(s) separated by newlines

        """
        sentences = []
        compound_sentence = ''
        # Multiple requests like "barn" and "back deck" can be in the same
        #   so append reports to a compound sentence.
        if intents['water']:
            sentences.append(self.report_water())
        # This simple test only reports temperature, nothing else
        if intents['location']:  # at least one location was explicitly named
            sentences.append(self.report_temperature(intents['location']))
        elif intents['temperature']:
            intents['location'].add('barn')
            intents['location'].add('deck')
            sentences.append(self.report_temperature(intents['location']))
        elif intents['unknown']:
            sentences.append(self.unknown_words(intents['unknown']))
        compound_sentence = ' '.join(sentences)
        if compound_sentence:
            return compound_sentence
        else:  # compound_sentence is still empty, so return "empty" message
            return "Couln't understand that. Could you try rewording it?"

    def parse_intents(self, request):
        """
        For a given request, parse the request into a dictionary of a
        limited number of concepts that capture the intent of the words in
        the request.

        Parser is very simple for testing and developing the other parts of the
        librarian. It will be replaced with a more elaborate and accurate intent
        parser later. The current algorithm is a simple "set of words" keyword
        match. Given the initial system goals of water management, motion
        detection and temperature / humidity measurement, keyword match style
        intent parsing is adequate.

        Parameters:
            request (str): a request text conntaining one or more words

        Returns:
            intents (dict): a dictionary
                Each key is a canonical intent word like 'water', 'temperature'
                Each value is a set of words in the request that matched a key
        """
        punctuation_pattern = ' |\.$|\. |, |\/|\(|\)|\'|\"|\!|\?|\+'
        ltext = request.lower()
        list_of_words = [w for w in re.split(punctuation_pattern, ltext) if w]
        list_of_words = self.remove_stopwords(list_of_words)
        request_words = set(list_of_words)
        water_words = {'water', 'flow', 'flowing', 'watering', 'meter'}
        temperature_words = {'temp', 'temps', 'temperature', 'hot', 'cold'}
        location_words = {'deck', 'barn', 'garage', 'office', 'front'
                    'driveway', 'grapes', 'downstairs'}  # imagenode locations
        location_helpers = {'inside', 'outside', 'door', 'in', 'front', 'back',
                    'behind', 'mailbox'}  # related location words
        # open_words = {'open', 'closed'}
        # light_words = {'dark', 'lit', 'light', 'lighted'}
        # motion_words = {'moving', 'motion'}
        # power_words = {'power', 'electricity'}
        # on_off_words = {'on', 'off'}
        # greeting_words = {'hi', 'hello', 'hey', 'how', 'hows', 'whats'}
        # goodbye_words = {'goodbye', 'bye', 'see', 'so', 'ttfn', 'quit', 'exit'}
        # help_words = {'help'}
        known_words = water_words | temperature_words | location_words
        known_words = known_words | location_helpers

        intents = dict() # keys are word types, values are sets of words
        # Use set intersection between request_words and response words to
        # set intents for specific response categories
        intents['water'] = set(request_words & water_words)
        intents['temperature'] = set(request_words & temperature_words)
        intents['location'] = set(request_words & location_words)
        intents['location_helpers'] = set(request_words & location_helpers)
        intents['unknown'] = request_words.difference(known_words)
        # intents['open'] = set(request_words & open_words)
        # intents['light'] = set(request_words & light_words)
        # intents['motion'] = set(request_words & motion_words)
        # intents['power'] = set(request_words & power_words)
        # intents['greeting'] = set(request_words & greeting_words)
        # intents['goodbye'] = set(request_words & goodbye_words)
        # intents['on_off'] = set(request_words & on_off_words)
        # intents['help'] = set(request_words & help_words)


        self.cleanup_intents(intents)  # clean up some specific word combos
        # for testing:
        # print('Printing intents dictionary:')
        # pprint.pprint(intents)
        # print('type(intents["water"]):', type(intents['water']))
        return intents

    def cleanup_intents(self, intents):
        # Do simple minded cleanup of some specific words & word combinations.
        # Also replace synonyms with "canonical names" for things.
        # This REALLY needs a better and more elegant algorithm...
        # Since all intents are sets, set.add(canonical name) handles synonyms
        # NOTE: this cleanup is specific to reporting temperature for testing.
        #  it will need to change to include reporting of motion, for example.
        if intents['location_helpers']:  # there was at least one; map them
            lh = intents['location_helpers']  # set of words
            if 'back' in lh:
                intents['location'].add('deck')
            if any(word in lh for word in ('in', 'inside')): # inside temp
                intents['location'].add('office')  # is temperature in office
                intents['location'].add('garage')  # and garage
            if 'outside' in lh:  # if asked about outside, report 2 outside locs
                intents['location'].add('deck')
                intents['location'].add('barn')

    def xf(self, motion):
        if motion == 'moving':
            return 'flowing'
        else:
            return 'off'

    def report_water(self):
        dt_now = datetime.now()
        (current, previous) = self.data.fetch_event_data('WaterMeter', 'motion')
        # current and previous are both tuples, where each
        #   tuple is (datetime, status), where status is moving or still
        status_now = self.xf(current[1])
        if not current:  # did not get a correct water tuple back, so
            return previous  # return the error message stored in previous
        elif previous:  # got both a present water value AND a previous one
            status_prev = self.xf(previous[1])
            when = previous[0]  # datetime of previous water event
            if when.day == dt_now.day:
                diff = '. '
            elif dt_now.day - when.day == 1:
                diff = ' yesterday. '
            else:
                diff = ' on {0}/{1}. '.format(when.month, when.day)
            reply = 'Water is {0}; last time {1} was at {2}{3}'.format(
                status_now, status_prev, when.strftime('%I:%M %p').lstrip('0'), diff)
        else:  # got a current water value, but not a previous one
            reply = 'Water is {0}; last status unknown'.format(status_now)
        return reply

    def report_temperature(self, locations):
        """ report temperature by location

        This is a very awkward test matching of location and temperature.
        Needs to be made much more sophistcated than if / else / etc.

        Parameters:
          locations (set): location words (each a str)

        Returns:
          reply (str): Sentences reporting temperatures for all the locations.

        """
        compound_reply = ''
        # for all locations, report temperature; Then remove the reported
        # location from the set of locations and repeat until all are reported.
        while locations:  # while there are any locations not yet reported
            word = locations.pop()
            if word.startswith('barn'):
                (current, previous) = self.data.fetch_event_data('barn', 'Temp')
                if current:
                    reply = 'Temperature behind barn is {0}.'.format(current[1])
                else:
                    reply = 'No current barn temperature available.'
            if word.startswith('deck'):
                (current, previous) = self.data.fetch_event_data('backdeck', 'Temp')
                if current:
                    reply = 'Temperature on back deck is {0}.'.format(current[1])
                else:
                    reply = 'No current back deck temperature available.'
            if word.startswith('garage'):
                (current, previous) = self.data.fetch_event_data('garage', 'Temp')
                if current:
                    reply = 'Temperature in garage is {0}.'.format(current[1])
                else:
                    reply = 'No current garage temperature available.'
            if word.startswith('office'):
                (current, previous) = self.data.fetch_event_data('jeffoffice', 'Temp')
                if current:
                    reply = 'Temperature inside house is {0}.'.format(current[1])
                else:
                    reply = 'No current inside temperature available.'
            compound_reply = ' '.join([compound_reply, reply])
            if len(locations) < 1:  # popped all locations; none left
                break
        return compound_reply.strip()

    def unknown_words(self, unknowns):
        """ report unknown words as such in reply

        Parameters:
          unknowns (set): unknown words (each a str)

        Returns:
          reply (str): Sentence reporting the unknown words

        """

        if len(unknowns) == 1:
            reply = "Don't know " +  '"' + unknowns.pop() + '".'
        else:
            reply = "Don't know " + '"' + '" or "'.join(unknowns) + '".'
        return reply

    def remove_stopwords(self, words):
        """ remove "stop words" from a list of words

        Parameters:
          words (list): a list of words (each a str)

        Returns:
          non_stop_words (list): list of words (each a str)

        """
        stopwords = ['i', 'me', 'my', 'myself', 'we', 'our', 'ours', 'ourselves',
        'you', "you're", "you've", "you'll", "you'd", 'your', 'yours', 'yourself',
        'yourselves', 'he', 'him', 'his', 'himself', 'she', "she's", 'her',
        'hers', 'herself', 'it', "it's", 'its', 'itself', 'they', 'them', 'their',
        'theirs', 'themselves', 'what', 'which', 'who', 'whom', 'this', 'that',
        "that'll", 'these', 'those', 'am', 'is', 'are', 'was', 'were', 'be',
        'been', 'being', 'have', 'has', 'had', 'having', 'do', 'does', 'did',
        'doing', 'a', 'an', 'the', 'and', 'but', 'if', 'or', 'because', 'as',
        'until', 'while', 'of', 'at', 'by', 'for', 'with', 'about', 'against',
        'between', 'into', 'through', 'during', 'before', 'after', 'above',
        'below', 'to', 'from', 'up', 'down', 'in', 'out', 'on', 'off', 'over',
        'under', 'again', 'further', 'then', 'once', 'here', 'there', 'when',
        'where', 'why', 'how', 'all', 'any', 'both', 'each', 'few', 'more',
        'most', 'other', 'some', 'such', 'no', 'nor', 'not', 'only', 'own',
        'same', 'so', 'than', 'too', 'very', 's', 't', 'can', 'will', 'just',
        'don', "don't", 'should', "should've", 'now', 'd', 'll', 'm', 'o', 're',
        've', 'y', 'ain', 'aren', "aren't", 'couldn', "couldn't", 'didn',
        "didn't", 'doesn', "doesn't", 'hadn', "hadn't", 'hasn', "hasn't",
        'haven', "haven't", 'isn', "isn't", 'ma', 'mightn', "mightn't", 'mustn',
        "mustn't", 'needn', "needn't", 'shan', "shan't", 'shouldn', "shouldn't",
        'wasn', "wasn't", 'weren', "weren't", 'won', "won't", 'wouldn',
        "wouldn't"]
        non_stop_words = [word for word in words if not word in stopwords]
        return non_stop_words
