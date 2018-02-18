from os.path import dirname
from mycroft.skills.core import MycroftSkill
from mycroft.skills.core import intent_handler, intent_file_handler
from adapt.intent import IntentBuilder
from mycroft.audio import wait_while_speaking
from mycroft.configuration import ConfigurationManager
from mycroft.util import play_wav, resolve_resource_file
from mycroft.util.log import getLogger
from subprocess import Popen, PIPE
from ctypes import *
from contextlib import contextmanager
from os import environ, path
import pyaudio
from pocketsphinx.pocketsphinx import *
from sphinxbase.sphinxbase import *
import sys
from websocket import create_connection
import requests
import json
import random
import time
from HTMLParser import HTMLParser

__author__ = 'tjoen'

LOGGER = getLogger(__name__)

validmc = [ '1', '2', '3', '4']
yesno = [ 'yes', 'no']
score = 0

config = ConfigurationManager.get()
ERROR_HANDLER_FUNC = CFUNCTYPE(None, c_char_p, c_int, c_char_p, c_int, c_char_p)

def py_error_handler(filename, line, function, err, fmt):
    pass

c_error_handler = ERROR_HANDLER_FUNC(py_error_handler)

@contextmanager
def noalsaerr():
    asound = cdll.LoadLibrary('libasound.so')
    asound.snd_lib_error_set_handler(c_error_handler)
    yield
    asound.snd_lib_error_set_handler(None)

class LsttSkill(MycroftSkill):
    def __init__(self):
        super(LsttSkill, self).__init__(name="LsttSkill")
        LOGGER.info("Starting Lstt")

    def initialize(self):
	lstt_intent = IntentBuilder("LsttIntent").\
            require("LsttKeyword").build()
        self.register_intent(lstt_intent, self.handle_lstt_intent)
	
    def invalid(self):
        self.speak("I did not understand you.")
        wait_while_speaking()
	p = self.runpocketsphinx("Please choose 1, 2, 3 or 4.", False, validmc)
        self.settings['myanswer'] = p
        return p
	
    def repeat(self):
        self.speak('I will repeat the question')
        wait_while_speaking()
        p = self.repeatquestion( self.settings.get('cat'), self.settings.get('question'), self.settings.get('answers'), self.settings.get('correct_answer'))
        self.settings['myanswer'] = p
        return p

    def askstop(self):
	response = self.runpocketsphinx("Would you like to stop?", False, yesno)
	if response == 'yes':
	    self.endgame()
	else:
	    p= self.runpocketsphinx("Choose 1,2,3 or 4", False, validmc)
            self.settings['myanswer'] = p
            return p
	
    def help(self):
	p = self.runpocketsphinx("I can not help you. What is your answer?", False, validmc)
        return p

    def start(self):
	response = self.runpocketsphinx("Would you like to restart?", False, yesno)
	if response == 'yes':
	    self.handle_trivia_intent()
	else:
	    p = self.runpocketsphinx("Choose 1,2,3 or 4", False, validmc)
            self.settings['myanswer'] = p
            return p
	
    def mychoice(self, x):
        try:
            return {
        'ONE': '1',
        'TWO': '2',
        'THREE': '3',
        'FOUR': '4',
        'FIVE': '5',
        'SIX': '6',
        'SEVEN': '7',
        'EIGHT': '8',
        'NINE': '9',
        'TEN': '10',
        'REPEAT': 'repeat',
        'STOP': 'stop',
        'PAUZE': 'pauze',
        'END': 'stop',
        'START': 'start',
        'QUIT': 'stop',
        'NEVER': 'invalid',
        'MIND': 'invalid',
        'HELP': 'help',
        'PLAY': 'start',
        'YES': 'yes',
        'NO': 'no',
            }[x]
        except KeyError:
            return 'invalid'

    def wsnotify(self, msg):
        uri = 'ws://localhost:8181/core'
        ws = create_connection(uri)
        print "Sending " + msg + " to " + uri + "..."
        data = "{}"
        message = '{"type": "' + msg + '", "data": ' + data +'}'
        result = ws.send(message)
        print "Receiving..."
        result =  ws.recv()
        print "Received '%s'" % result
        ws.close()

    def handle_record_begin(self):
        LOGGER.info("Lsst - Begin Recording...") 
        # If enabled, play a wave file with a short sound to audibly
        # indicate recording has begun.
        if config.get('confirm_listening'):
            file = resolve_resource_file(
                config.get('sounds').get('start_listening'))
            if file:
                play_wav(file)
        self.wsnotify('recognizer_loop:record_begin')

    def handle_record_end(self):
        LOGGER.info("Lsst - End Recording...")
        self.wsnotify('recognizer_loop:record_end')

    def runpocketsphinx(self, msg, speakchoice, arr):
        while self.settings.get('running'):
            time.sleep(0.5)
            if not self.settings.get('running'):
                break

        self.speak(msg)
        wait_while_speaking()
        HOMEDIR = '/home/pi/'
        config = Decoder.default_config()
        config.set_string('-hmm', '/usr/local/lib/python2.7/site-packages/mycroft_core-0.9.17-py2.7.egg/mycroft/client/speech/recognizer/model/en-us/hmm')
        config.set_string('-lm', path.join(HOMEDIR, 'localstt.lm'))
        config.set_string('-dict', path.join(HOMEDIR, 'localstt.dic'))
        config.set_string('-logfn', '/dev/null')
        decoder = Decoder(config)

        with noalsaerr():
            p = pyaudio.PyAudio()
        stream = p.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, frames_per_buffer=1024)
        stream.start_stream()
        self.handle_record_begin()
      
        in_speech_bf = False
        decoder.start_utt()
        while True:
            buf = stream.read(1024)
            if buf:
                decoder.process_raw(buf, False, False)
                if decoder.get_in_speech() != in_speech_bf:
                    in_speech_bf = decoder.get_in_speech()
                    if not in_speech_bf:
                        decoder.end_utt()
                        #print 'Result:', decoder.hyp().hypstr
                        utt = decoder.hyp().hypstr
                        decoder.start_utt()
                        if utt.strip() != '':
                            self.handle_record_end()
                            stream.stop_stream()
                            stream.close()
                            p.terminate()
                            reply = utt.strip().split(None, 1)[0]
			    if speakchoice:
                                self.speak( "Your answer is " + reply )
                                wait_while_speaking()
	                    selection = self.mychoice(reply)
                            if selection in arr:
                                # Do the thing
                                self.settings['myanswer'] = selection
                                return selection
                            elif selection == 'repeat':
                                self.repeat()
                            elif selection == 'stop':
                                self.askstop()
                            elif selection == 'help':
                                self.help()
                            elif selection == 'start':
                                self.start()
                            else:
                                self.invalid()                            
                            break
            else:
                break
        decoder.end_utt()

    def play(self, filename):
        play_wav( self.settings.get('resdir')+filename )
    
    def score(self, point):
        global score
        score = score+point
        self.enclosure.deactivate_mouth_events()
        self.enclosure.mouth_text( "SCORE: "+str(score) )
        return

    def wrong(self, right_answer):
        self.enclosure.mouth_text( "WRONG!" )
        self.speak_dialog("incorrect")
        wait_while_speaking()
        self.play( 'false.wav' )
        self.speak("The answer is "+right_answer)
        wait_while_speaking()
        return

    def right(self):
        self.enclosure.mouth_text( "CORRECT!" )
        self.speak_dialog("correct")
        wait_while_speaking()
        self.play( 'true.wav' )
        self.score(1)
        return    

    def preparequestion(self, category, question, answers, right_answer):
        h = HTMLParser()
        quest = h.unescape( question )
        time.sleep(1.5)
        self.speak("The category is "+ category+ ". " + quest )
        wait_while_speaking()
        correct_answer = h.unescape( right_answer )
        allanswers = list()
        allanswers.append(h.unescape(right_answer))
        for a in answers:
            allanswers.append(h.unescape(a))
        random.shuffle(allanswers)
        self.settings['running'] = True
        self.settings['cat'] = category
        self.settings['question'] = quest
        self.settings['answers'] = allanswers
        self.settings['correct_answer'] = correct_answer
        self.askquestion( category, quest, allanswers, correct_answer )
    
    def repeatquestion(self, category, question, answers, right_answer):
        time.sleep(1)
        self.speak( question )
        wait_while_speaking()
        i=0
        ans = ""
        for a in answers:
            i = i + 1
            self.speak(str(i) + ".    " + a)
            wait_while_speaking()
        self.settings['running'] = False
        response = self.runpocketsphinx("Choose 1,2,3 or 4.", False, validmc)
        # response = self.settings.get('myanswer')
        # self.speak("Your choice is "+ str(response))
        return response

    def askquestion( self, category, quest, allanswers, correct_answer):
        i=0
        ans = ""
        for a in allanswers:
            i = i + 1
            self.speak(str(i) + ".    " + a)
            wait_while_speaking()
        self.settings['running'] = False
        response = self.runpocketsphinx("Choose 1,2,3 or 4.", False, validmc)
        response2 = self.settings.get('myanswer')
        self.speak("Your choice is "+ str(response2))
        wait_while_speaking()
        self.enclosure.deactivate_mouth_events()
        if correct_answer == allanswers[int(response2)-1]:
            self.right()
        else:
            self.wrong(correct_answer)
        return 

    def endgame(self):
        self.enclosure.activate_mouth_events()
        self.play( 'end.wav' )
        self.enclosure.mouth_text( "SCORE: "+str(score) )
        self.speak("You answered " +str(score)+ " questions correct")
        wait_while_speaking()
        self.speak("Thanks for playing!")
        wait_while_speaking()
        self.stop()
    
    def handle_trivia_intent(self):
        self.settings['cat'] = None
        self.settings['question'] = None
        self.settings['answers'] = None
        self.settings['myanswer'] = None
        self.settings['correct_answer'] = None
        self.settings['resdir'] = '/opt/mycroft/skills/lstt-skill/res/'
        self.play( 'intro.wav' )
        self.enclosure.deactivate_mouth_events()
        # Display icon on faceplate
        self.enclosure.mouth_display("aIMAMAMPMPMPMAMAAPAPADAAIOIOAAAHAMAMAHAAIOIOAAAPAFAFAPAAMLMLAAAAAA", x=1, y=0, refresh=True)
        time.sleep(1.5) 
        url = "https://opentdb.com/api.php?amount=5&type=multiple"
        headers = {'Accept': 'text/plain'}
        r = requests.get(url, headers)
        m = json.loads(r.text)
        questions = m['results'];
        global score
        score = 0
        self.speak("Okay, lets play a game of trivia. Get ready!")
        wait_while_speaking()
        for f in questions:
            self.enclosure.activate_mouth_events()
            self.enclosure.mouth_reset()
            self.preparequestion( f['category'], f['question'], f['incorrect_answers'], f['correct_answer'])
        self.endgame()
    
    def stop(self):
        self.enclosure.activate_mouth_events()
        self.enclosure.mouth_reset()
        self.enclosure.reset()    
        command = 'service mycroft-speech-client start'.split()
        p = Popen(['sudo', '-S'] + command, stdin=PIPE, stderr=PIPE, universal_newlines=True)
        LOGGER.info("Starting speech-client" )
        pass

    def handle_lstt_intent(self, message):
        command = 'service mycroft-speech-client start'.split()
        p = Popen(['sudo', '-S'] + command, stdin=PIPE, stderr=PIPE, universal_newlines=True)
        LOGGER.info("Stopping speech-client")
	self.handle_trivia_intent()


def create_skill():
      return LsttSkill()
