import sys
import random
from PySide6 import QtCore, QtWidgets, QtGui
from queue import Queue
from threading import Thread
import pyaudio
import subprocess
import json
from vosk import Model, KaldiRecognizer
import time


class MyWidget(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        self.hello = ["Hallo Welt", "Hei maailma", "Hola Mundo", "Привет мир"]

        self.record_button = QtWidgets.QPushButton("Record")
        self.stop_button = QtWidgets.QPushButton("Stop")
        self.text = QtWidgets.QLabel("Hello World", alignment=QtCore.Qt.AlignCenter)

        self.layout = QtWidgets.QVBoxLayout(self)

        self.button_layout = QtWidgets.QHBoxLayout(self)
        self.button_layout.addWidget(self.record_button)
        self.button_layout.addWidget(self.stop_button)

        self.layout.addLayout(self.button_layout)
        self.layout.addWidget(self.text)

        self.record_button.clicked.connect(self.magic)
        self.stop_button.clicked.connect(self.stop_recording)

        # audio configurations
        self.messages = Queue()
        self.recordings = Queue()
        self.CHANNELS = 1
        self.FRAME_RATE = 16000
        self.RECORD_SECONDS = 20
        self.AUDIO_FORMAT = pyaudio.paInt16
        self.SAMPLE_SIZE = 2

        self.model = Model(model_name="vosk-model-en-us-0.22")
        self.rec = KaldiRecognizer(self.model, self.FRAME_RATE)
        self.rec.SetWords(True)
        self.output_text = ""

    @QtCore.Slot()
    def magic(self):
        self.messages.put(True)
        record = Thread(target=self.record_microphone)
        record.start()
        self.text.setText("Started recording")

        transcribe = Thread(target=self.speech_recognition)
        transcribe.start()

        self.text.setText("Started transcribing")

    @QtCore.Slot()
    def record_microphone(self, chunk=1024):
        p = pyaudio.PyAudio()
        stream = p.open(
            format=self.AUDIO_FORMAT,
            channels=self.CHANNELS,
            rate=self.FRAME_RATE,
            input=True,
            input_device_index=0,
            frames_per_buffer=chunk,
        )

        frames = []

        while not self.messages.empty():
            data = stream.read(chunk)
            frames.append(data)
            if len(frames) >= (self.FRAME_RATE * self.RECORD_SECONDS) / chunk:
                self.recordings.put(frames.copy())
                frames = []

        stream.stop_stream()
        stream.close()
        p.terminate()

    @QtCore.Slot()
    def stop_recording(self, data):
        self.messages.get()
        self.text.setText("Stopped recording")

    @QtCore.Slot()
    def speech_recognition(self):
        while not self.messages.empty():
            frames = self.recordings.get()

            self.rec.AcceptWaveform(b"".join(frames))
            result = self.rec.Result()
            text = json.loads(result)["text"]

            print(text)

            # cased = subprocess.check_output(
            #     "python recasepunc/recasepunc.py predict recasepunc/checkpoint",
            #     shell=True,
            #     text=True,
            #     input=text,
            # )
            self.output_text += text
            self.text.setText(self.output_text)
            time.sleep(0.5)


if __name__ == "__main__":
    try:
        app = QtWidgets.QApplication([])

        widget = MyWidget()
        widget.resize(800, 600)
        widget.show()

        sys.exit(app.exec())
    except KeyboardInterrupt:
        pass
