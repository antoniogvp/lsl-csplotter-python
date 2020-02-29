# -*- coding: utf-8 -*-
"""
@author: Antonio
"""
import numpy as np
from scipy import special, interpolate

class BandPassFilter:
    def __init__(self, freqFilterParams, srate):
        self.B = []
        if(len(freqFilterParams) is 4):
            # Design moving-average (low-pass) filter
            self.B = self.designBPF(freqFilterParams, srate, 20, True)
            
        elif(len(freqFilterParams) is 1):
            # Design band-pass filter
            self.B = np.asarray([1]*freqFilterParams[0])/max(1,freqFilterParams[0])
            self.B = np.transpose(self.B)
            
        else:
            print("Error: filter paramters were not passed correctly.")
            
            
    def designBPF(self,freqs,srate,atten,minphase):
        # get frequencies and amplitudes
        for n in range(4):
            freqs[n] = min(freqs[n]*2/srate,0.95)
        
        # design Kaiser window for smallest transition band
        pos = np.argmin(np.diff(freqs))
        wnd = self.designKaiser(freqs[pos],freqs[pos+1],atten,False)
        
        # design FIR filter with that window
        freqs.insert(0,0)
        freqs.append(1)
        B = self.designFIR(len(wnd)-1,freqs,[0,0,1,1,0,0],wnd)
        
        # transform to minimum-phase design
        if minphase:
            n = len(B)
            
            wnd = [1] + [2]*int((n+n%2)/2-1) + [1]*(1-n%2) + [0]*int((n+n%2)/2-1)
            B = np.real(np.fft.ifft(np.exp(np.fft.fft(np.asarray(wnd)*np.real(
                    np.fft.ifft(np.log(abs(np.fft.fft(B))+np.power(10,-atten/10))))))))
            
        return B
        
    def designFIR(self,N,F,A,W):
        nfft = max(512,np.power(2,np.ceil(np.log(N)/np.log(2))))
        #odd = False
        
        # calculate interpolated frequency response
        fun = interpolate.pchip(np.round(np.asarray(F)*nfft),np.asarray(A))
        rng = np.arange(nfft+1)
        F = fun(rng)
        
        # set phase & transform into time domain
        F = F * np.exp(-(0.5*N)*np.sqrt(-1+0j)*np.pi*rng/nfft)
        
        B = np.real(np.fft.ifft(np.append(F, np.conj(F[-2:0:-1]))))
        
        # apply window to kernel
        B = B[0:N+1]*W
        
        return B
        
    def designKaiser(self,lo,hi,atten,odd):
        # design a Kaiser window for a low-pass FIR filter
        # determine beta parameter of the window
        if atten < 21:
            beta = 0
        elif atten <= 50:
            beta = np.power(0.5842*(atten-21),0.4) + 0.07886*(atten-21)
        else:
            beta = 0.1102*(atten-8.7)
            
        # determine the number of points
        N = round((atten-7.95)/(2*np.pi*2.285*(hi-lo)))+1
        if odd and not(np.mod(N,2)):
            N = N+1
        
        # design the window
        W = special.iv(0,beta*np.sqrt(1-np.power(2*((np.array(
                list(range(0,N)), dtype='f'))/(N-1))-1,2)))/special.iv(0,beta)
        return W
        
    def returnFilter(self):
        return self.B