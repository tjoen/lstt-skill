## Trivia skill with local stt - WIP
This skill starts a game of general trivia with local speech-to-text.

## Description 
At the moment, the skill will ask you 3 "general knowledge" questions. You can answer by choosing 1,2,3 or 4.
Yes, No, Stop, Repeat and Start should also work.

This testskill uses mycrofts pocketsphinx STT with a small dict.

It uses a localstt.dic (dictionary) and localstt.lm (language model) in the res folder.

## Current state
Working features:
- Version seems to work fine, the skill disables the speechclient and audio service during the skill
- great speed improvement on speech results.

## Known issues:
Could probably be much more efficient, and much cleaner.

## Examples 
* "Hey Mycroft, start local speech"
* "Hey Mycroft, local speech test"

## Credits 
Theun Kohlbeck, https://github.com/tjoen
Steen Bentall, https://github.com/barricados

## Require 
platform_mark1 platform_picroft platform_plasmoid 
