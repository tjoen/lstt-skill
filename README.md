## Trivia skill with local stt
This skill starts a game of general trivia with local speech-to-text.

## Description 
This skill uses mycrofts pocketsphinx STT with a small dict.

It uses a localstt.dic (dictionary) and localstt.lm (language model) in the res folder.
It shuts now down the speech recognition with naptime when the skill starts, and wakes it up when ending it.

At the moment, the skill will ask you 3 questions. 
You can answer by choosing 1,2,3 or 4.

Yes, no, stop/quit/end, repeat and start/play should also work.

This started out as an experiment, checking if a faster method could make the  game more playable. 
And it actually does seem to work pretty good. 

Translations might be a problem with this method, but this skill uses questions in english. 
[JarbasAI](https://github.com/JarbasAl) just made a very nice local listener that will be implemented in the near future.
[More info on that here](https://github.com/JarbasAl/local_listener)

## Current state
Working features:
- Version seems to work fine, the skill invokes naptime during the skill
- great speed improvement on speech results.

## Known issues:
Could probably be much more efficient, and much cleaner.

## Examples 
* "Hey Mycroft, start local speech"
* "Hey Mycroft, play trivia"
* "Hey Mycroft, game of trivia"

## Credits 
Theun Kohlbeck, https://github.com/tjoen
Steen Bentall, https://github.com/barricados

## Require 
platform_mark1 platform_picroft platform_plasmoid 
