"""Explicit output-device playback, independent of the capture engine."""
import os
import subprocess
import threading
from pathlib import Path
import numpy as np


def output_devices(sd):
    apis = sd.query_hostapis()
    result=[]
    for index, device in enumerate(sd.query_devices()):
        if device['max_output_channels']:
            result.append((index, dict(name=device['name'],hostapi=apis[device['hostapi']]['name']),device))
    return result


def resolve_output(sd, selection):
    if selection is None:
        index = sd.default.device[1]
        if index<0: raise ValueError('No system-default playback device is available')
        return index,sd.query_devices(index,'output')
    matches=[(index,device) for index,key,device in output_devices(sd) if key==selection]
    if len(matches)!=1:
        raise ValueError('Saved playback device is unavailable or ambiguous. Refresh and select an output in Playback settings.')
    return matches[0]


class Player:
    def __init__(self):
        self.status='Playback stopped'
        self.cancel=threading.Event()
        self.thread=None
        self.process=None
        self.lock=threading.Lock()

    def is_idle(self):
        return not (self.thread and self.thread.is_alive())

    def stop(self):
        self.cancel.set()
        with self.lock:
            if self.process and self.process.poll() is None:
                try:
                    self.process.terminate()
                except ProcessLookupError:
                    pass

    def play(self,path,config):
        self.stop()
        if self.thread:
            self.thread.join(timeout=3)
            if self.thread.is_alive(): raise ValueError('Previous playback is stopping. Try again shortly.')
        path=Path(path).resolve()
        if not path.is_file(): raise ValueError('Recording file is missing')
        self.cancel=threading.Event()
        self.status='Opening playback device…'
        self.thread=threading.Thread(target=self._run,args=(path,config,self.cancel),daemon=True)
        self.thread.start()

    def _run(self,path,config,cancel):
        decoder=None
        try:
            import sounddevice as sd
            from .engine import ffmpeg_exe
            index,device=resolve_output(sd,config.get('playback',{}).get('device'))
            rate=int(device['default_samplerate'])
            channels=min(2,int(device['max_output_channels']))
            sd.check_output_settings(device=index,channels=channels,dtype='float32',samplerate=rate)
            if cancel.is_set(): return
            with sd.OutputStream(device=index,channels=channels,dtype='float32',samplerate=rate) as stream:
                flags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0
                with self.lock:
                    if cancel.is_set(): return
                    decoder=subprocess.Popen([ffmpeg_exe(config),'-hide_banner','-loglevel','error','-nostdin',
                        '-protocol_whitelist','file,pipe','-i',str(path),'-vn','-f','f32le','-acodec','pcm_f32le',
                        '-ar',str(rate),'-ac',str(channels),'pipe:1'],stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,creationflags=flags)
                    self.process=decoder
                self.status='Playing: '+path.name+' → '+device['name']
                while not cancel.is_set():
                    block=decoder.stdout.read(1024*channels*4)
                    if not block: break
                    if len(block)%(channels*4): raise ValueError('Incomplete decoded audio frame')
                    if not cancel.is_set(): stream.write(np.frombuffer(block,dtype='<f4').reshape(-1,channels))
                if cancel.is_set(): stream.abort()
                elif decoder.wait(timeout=5): raise ValueError('Audio decoding failed; recording file was preserved')
            self.status='Playback stopped' if cancel.is_set() else 'Playback finished'
        except Exception as error:
            self.status='Playback stopped' if cancel.is_set() else 'Playback error: '+str(error)
        finally:
            if decoder:
                if decoder.poll() is None:
                    decoder.kill()
                decoder.wait(timeout=5)
                if decoder.stdout: decoder.stdout.close()
            with self.lock:
                if self.process is decoder: self.process=None
            if cancel.is_set(): self.status='Playback stopped'

    def close(self):
        self.stop()
        if self.thread: self.thread.join(timeout=3)
