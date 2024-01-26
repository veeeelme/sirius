import vosk
import json
from pyaudio import *
import numpy as np
import time
import gtts
from pydub import AudioSegment
from pydub.playback import play
from pydub.silence import detect_silence
import datetime
from pydub.silence import detect_silence
import webbrowser
import random
import weather
import json
import newsapi
import pvporcupine


class AudioRecorder():
    def __init__(self, porcupine_instance, max_silence_duration=1500, sample_rate=16000, chunk_size=1024, silence_thresh=1000):
        self.porcupine = porcupine_instance
        self.max_silence_duration = max_silence_duration
        self.sample_rate = sample_rate
        self.chunk_size = chunk_size
        self.silence_thresh = silence_thresh
        self._frames = b''
        self._start_time = None
        self.stream = None
        self.p = None

    def add_data_to_frames(self, new_data):
        self._frames += new_data

    def is_silence(self, audio_chunk, silence_thresh=-300, energy_thresh=1):
        audio_segment = AudioSegment(audio_chunk.tobytes(
        ), sample_width=audio_chunk.dtype.itemsize, channels=1, frame_rate=self.sample_rate)
        silent_ranges = detect_silence(
            audio_segment, silence_thresh=silence_thresh)

        # Check if there are any silent ranges
        return not any(silent_range[1] - silent_range[0] >= self.max_silence_duration for silent_range in silent_ranges), len(silent_ranges) > 0

    def detect_wake_word(self, porcupine, audio_data, chunk_size=512):
        audio_data_int16 = np.frombuffer(audio_data, dtype=np.int16)
        keyword_index = porcupine.process(audio_data_int16)
        return keyword_index >= 0

    def record_audio(self, max_silence_duration=3000, sample_rate=16000, chunk_size=512, silence_thresh=1000):
        self.p = PyAudio()
        self.stream = self.p.open(format=paInt16,
                                  channels=1,
                                  rate=sample_rate,
                                  input=True,
                                  frames_per_buffer=chunk_size)

        self._frames = b''
        self._start_time = time.time()

        print("Recording...")

        try:
            while True:
                try:
                    data = self.stream.read(chunk_size)
                    audio_chunk = np.frombuffer(data, dtype=np.int16)

                    self.add_data_to_frames(new_data=data)

                    if not self.is_silence(audio_chunk):
                        self._start_time = time.time()
                    elif time.time() - self._start_time >= max_silence_duration / 1000.0:
                        break

                    if self.detect_wake_word(porcupine, data, chunk_size):
                        print("Wake word detected! Listening for commands...")
                        process_voice_commands(self)
                        break
                except KeyboardInterrupt:
                    print("Recording interrupted.")
                    break

        finally:
            print("Recording finished.")
            if self.stream and self.stream.is_active():
                self.stream.stop_stream()
                self.stream.close()
                print("Audiorecognizer.stream closed.")

            if self.p:
                self.p.terminate()
                print("PyAudio terminated.")

        return self._frames, self.p, self.stream

    def recognize_speech(self, audio_data):
        path_to_model = "/Users/dimapogarskiy/vosk-model-en-us-0.22-lgraph"
        model = vosk.Model(path_to_model)
        recognizer = vosk.KaldiRecognizer(model, 16000)
        recognizer.AcceptWaveform(audio_data)

        result = json.loads(recognizer.Result())
        recognized_text = result.get('text', '')

        return recognized_text


def listen_for_wake_word(porcupine, recognizer):
    try:
        while True:
            try:
                audio_recorder_data, _, _ = recognizer.record_audio()
                keyword_index = porcupine.process(audio_recorder_data)

                if keyword_index >= 0:
                    print("Wake word detected! Listening for commands...")
                    process_voice_commands(recognizer)
                    break
            except Exception:
                pass
    except KeyboardInterrupt:
        print("Listening interrupted.")


def process_voice_commands(recognizer):
    while True:
        speak('How can I help you?')
        audio_recorder_data, _, _ = recognizer.record_audio()

        recognized_text = recognizer.recognize_speech(
            audio_data=audio_recorder_data)
        print("Recognized text:", recognized_text)
        handle_commands(recognizer, recognized_text=recognized_text)


def speak(text: str):
    tts = gtts.gTTS(text, lang='en')
    tts.save('hello.wav')
    song = AudioSegment.from_file("hello.wav")

    return play(song)


def handle_commands(recognizer, recognized_text):
    while True:
        if 'hello' in recognized_text or 'hi ' in recognized_text:
            speak('Hello sir')

        elif 'wikipedia' in recognized_text:
            speak('What should i search?')
            audio_recorder_data, p, stream = recognizer.record_audio()
            recognized_text = recognizer.recognize_speech(
                audio_data=audio_recorder_data)
            speak(random.choice(welcome_list))
            speak('Searching Wikipedia...')
            webbrowser.open_new_tab(
                f'https://en.wikipedia.org/wiki/{recognized_text}')

        elif 'open google' in recognized_text:
            random_el = random.choice(welcome_list)
            print(random_el)
            speak(random_el)
            webbrowser.open_new_tab('https://www.google.com/')

        elif 'search in google' in recognized_text or 'searching google' in recognized_text:
            speak('What should i search?')
            audio_recorder_data, p, stream = recognizer.record_audio()
            recognized_text = recognizer.recognize_speech(
                audio_data=audio_recorder_data)
            random_el = random.choice(welcome_list)
            speak(random_el)
            print(random_el)
            webbrowser.open_new_tab(
                f'https://www.google.com/search?q={recognized_text}')

        elif 'open youtube' in recognized_text or 'open the youtube' in recognized_text:
            random_el = random.choice(welcome_list)
            print(random_el)
            speak(random_el)
            webbrowser.open_new_tab('https://www.youtube.com/')

        elif 'search in youtube' in recognized_text or 'search in egypt' in recognized_text or 'search youtube' in recognized_text:
            speak('What should i search?')
            audio_recorder_data, p, stream = recognizer.record_audio()
            recognized_text = recognizer.recognize_speech(
                audio_data=audio_recorder_data)
            random_el = random.choice(welcome_list)
            speak(random_el)
            print(random_el)
            webbrowser.open_new_tab(
                f'https://www.youtube.com/results?search_query={recognized_text}')

        elif 'the time' in recognized_text:
            strTime = datetime.datetime.now().strftime("%m/%d/%y and %H:%M:%S")
            print(f"Sir, the time is {strTime}")
            speak(f"Sir, the time is {strTime}")

        elif 'weather' in recognized_text or 'whether' in recognized_text:
            speak('Weather in what city you want to know')
            audio_recorder_data, p, stream = recognizer.record_audio()
            recognized_text = recognizer.recognize_speech(
                audio_data=audio_recorder_data)
            random_el = random.choice(welcome_list)
            weatherAPI = weather.API('2ba0d611070d4a21bc4172910230410')

            def get_weather(city):
                weather = weatherAPI.current(city)
                return f"\nTodays temperature is {weather['current']['temp_c']} celsius and kind of weather is {weather['current']['condition']['text']}."

            print(get_weather(recognized_text))
            speak(get_weather(recognized_text))

        elif 'news' in recognized_text or 'use' in recognized_text:
            api = newsapi.newsapi_client.NewsApiClient(
                api_key='6d4eafa463644b9081a941b680e60365')
            top_headlines = api.get_top_headlines(
                language='en', country='us', page_size=5, category='general')

            print("Here are some last news around the world:\n ")
            speak('Here are some last news around the world')
            for article in top_headlines["articles"]:
                title = article.get("title")
                description = article.get("description")
                print("Title:", title)
                print("Description:", description, '\n')

        recognizer = AudioRecorder(porcupine_instance=pvporcupine.Porcupine)
        porcupine = pvporcupine.create(
            access_key='BE0u16MJdu6hk1M9mVsfVOffxDphy3InpPr4c3jdSJrb+4ippdyUUg==',
            keywords=['hey siri'],
            sensitivities=[0.5]
        )
        listen_for_wake_word(porcupine, recognizer)


if __name__ == "__main__":
    recognizer = AudioRecorder(porcupine_instance=pvporcupine.Porcupine)
    welcome_list = ['Here you are', 'Just give me a second',
                    'Okay, here we go', 'Working on a request']
    porcupine = pvporcupine.create(
        access_key='BE0u16MJdu6hk1M9mVsfVOffxDphy3InpPr4c3jdSJrb+4ippdyUUg==',
        keywords=['hey siri'],
        sensitivities=[0.5]
    )

    listen_for_wake_word(porcupine, recognizer)
    if 'porcupine' in locals():
        porcupine.delete()
        print("Porcupine deleted.")
