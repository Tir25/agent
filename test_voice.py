"""
Voice Capture Test - Extended Listening
"""

print("=" * 60)
print("VOICE CAPTURE TEST")
print("=" * 60)

from app.services.voice.speaker import TextToSpeech
from app.services.voice.listener import VoiceListener

speaker = TextToSpeech(rate=150)
listener = VoiceListener()

if listener.initialize():
    speaker.speak("I am ready. Please speak now.")
    print("\n>>> LISTENING... Speak something! (5 seconds)")
    
    text = listener.listen(timeout_chunks=50)  # ~5 seconds
    
    if text:
        print(f'\n>>> RECOGNIZED: "{text}"')
        speaker.speak(f"You said: {text}")
    else:
        print("\n>>> No speech detected. Try speaking louder.")
    
    listener.close()
else:
    print("Failed to initialize listener")

print("\n" + "=" * 60)
