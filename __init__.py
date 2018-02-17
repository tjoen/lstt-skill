from os.path import dirname
from mycroft.skills.core import MycroftSkill
from mycroft.skills.core import intent_handler, intent_file_handler
from adapt.intent import IntentBuilder
from mycroft.audio import wait_while_speaking
from mycroft.configuration import ConfigurationManager
from mycroft.util import play_wav, resolve_resource_file
from mycroft.util.log import getLogger
import subprocess
from ctypes import *
from contextlib import contextmanager
from os import environ, path
import pyaudio
from pocketsphinx.pocketsphinx import *
from sphinxbase.sphinxbase import *


__author__ = 'tjoen'

LOGGER = getLogger(__name__)
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

    def runpocketsphinx(self):
        self.speak("starting local speech client")
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
                        print 'Result:', decoder.hyp().hypstr
                        utt = decoder.hyp().hypstr
                        decoder.start_utt()
                        if utt.strip() != '':
                            #print utt.strip()
                            reply = utt.strip().split(None, 1)[0]
                            self.speak( reply )
                            wait_while_speaking()
                            print(reply)
                            #selection = mychoice[reply]
                            stream.stop_stream()
                            stream.close()
                            self.handle_record_end()
                            p.terminate()
                            pygame.quit()
                            #self.stop() 
                            #selection()
                        #    break
            else:
                break
        decoder.end_utt()

    def handle_record_begin(self):
        LOGGER.info("Begin Recording...") 
        # If enabled, play a wave file with a short sound to audibly
        # indicate recording has begun.
        if config.get('confirm_listening'):
            file = resolve_resource_file(
                config.get('sounds').get('start_listening'))
            if file:
                play_wav(file)
        #ws.emit(Message('recognizer_loop:record_begin'))

    def handle_record_end(self):
        LOGGER.info("End Recording...")
        #ws.emit(Message('recognizer_loop:record_end'))

    def stop(self):
        #cmd_output = subprocess.check_output(['sudo', 'service', 'mycroft-speech-client', 'start']) 
        #cmd_output = cmd_output.decode('utf-8').strip('\n\r')
        #logger.info("Starting Speechclient"+ cmd_output )
        pass

    def handle_lstt_intent(self, message):
        #stop speech-client
        #cmd_output = subprocess.check_output(['sudo', 'service', 'mycroft-speech-client', 'stop']) 
        #cmd_output = cmd_output.decode('utf-8').strip('\n\r')
        #LOGGER.info("Stopping Speechclient"+ cmd_output )
        self.runpocketsphinx

def create_skill():
      return LsttSkill()