"""Kokoro English, native FP32 audio and tested Misaki pronunciation frontend."""
import numpy as np
import onnxruntime as ort
from kokoro_onnx import Kokoro
from misaki import en, espeak

class Engine:
    def __init__(self, assets, settings):
        self.settings=settings
        options=ort.SessionOptions()
        options.intra_op_num_threads=settings['threads']
        options.inter_op_num_threads=1
        session=ort.InferenceSession(str(assets/'kokoro-v1.0.onnx'),sess_options=options,
                                    providers=['CPUExecutionProvider'])
        if next(i.type for i in session.get_inputs() if i.name=='speed')!='tensor(float)':
            raise ValueError('Unexpected Kokoro model input format.')
        self.model=Kokoro.from_session(session,str(assets/'voices-v1.0.bin'))
        class FloatSpeedSession:
            def get_inputs(self): return session.get_inputs()
            def run(self, outputs, inputs):
                inputs=dict(inputs)
                inputs['speed']=np.asarray(inputs['speed'],dtype=np.float32)
                return session.run(outputs,inputs)
        self.model.sess=FloatSpeedSession()
        british=settings['voice'].startswith('b')
        self.g2p=en.G2P(trf=False,british=british,fallback=espeak.EspeakFallback(british=british))

    def synthesize(self,text):
        phonemes,_=self.g2p(text)
        if not phonemes.strip() or '❓' in phonemes:
            raise ValueError('Some text could not be pronounced. Try spelling out unusual symbols.')
        # Reject any truncation-prone chunk instead of silently dropping phonemes.
        from kokoro_onnx.config import MAX_PHONEME_LENGTH
        if any(len(chunk)>MAX_PHONEME_LENGTH for chunk in self.model._split_phonemes(phonemes)):
            raise ValueError('A phrase is too long. Add sentence punctuation and try again.')
        audio,sample_rate=self.model.create(phonemes,voice=self.settings['voice'],
            speed=self.settings['speed'],is_phonemes=True,trim=False)
        if sample_rate!=24000 or not audio.size or not np.isfinite(audio).all():
            raise ValueError('Invalid Kokoro audio.')
        return audio,sample_rate
