"""
Audio Enhancement Service
Service for enhancing audio quality and reducing noise.
"""

import asyncio
import os
import tempfile
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID
import numpy as np
import librosa
from pydub import AudioSegment
from pydub.effects import normalize
import soundfile as sf

from common.utils.logging import get_logger
from ..models.audio_processing import AudioEnhancementResult


logger = get_logger(__name__)


class AudioEnhancementService:
    """Service for enhancing audio quality"""
    
    def __init__(self):
        self.logger = get_logger(__name__)
        self.supported_formats = ['.wav', '.mp3', '.m4a', '.flac', '.ogg']
        self.enhancement_methods = {
            "noise_reduction": self._reduce_noise,
            "normalization": self._normalize_audio,
            "filtering": self._apply_filters,
            "compression": self._apply_compression
        }
    
    async def enhance_audio(
        self, 
        audio_file_path: str,
        enhancement_methods: Optional[List[str]] = None
    ) -> AudioEnhancementResult:
        """
        Enhance audio quality using specified methods
        
        Args:
            audio_file_path: Path to the input audio file
            enhancement_methods: List of enhancement methods to apply
            
        Returns:
            AudioEnhancementResult with enhancement details
        """
        start_time = datetime.utcnow()
        
        try:
            self.logger.info(f"Enhancing audio file: {audio_file_path}")
            
            # Validate input file
            if not self._validate_audio_file(audio_file_path):
                raise ValueError(f"Invalid audio file: {audio_file_path}")
            
            # Use default enhancement methods if none specified
            if enhancement_methods is None:
                enhancement_methods = ["normalization", "noise_reduction"]
            
            # Load audio
            audio_data, sample_rate = await self._load_audio(audio_file_path)
            
            # Apply enhancements
            enhanced_audio = audio_data.copy()
            applied_enhancements = []
            
            for method in enhancement_methods:
                if method in self.enhancement_methods:
                    try:
                        enhanced_audio = await self.enhancement_methods[method](
                            enhanced_audio, sample_rate
                        )
                        applied_enhancements.append(method)
                        self.logger.info(f"Applied {method} enhancement")
                    except Exception as e:
                        self.logger.warning(f"Failed to apply {method}: {str(e)}")
            
            # Save enhanced audio
            enhanced_file_path = await self._save_enhanced_audio(
                enhanced_audio, sample_rate, audio_file_path
            )
            
            # Calculate improvement score
            improvement_score = await self._calculate_improvement_score(
                audio_data, enhanced_audio
            )
            
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            
            return AudioEnhancementResult(
                original_audio_path=audio_file_path,
                enhanced_audio_path=enhanced_file_path,
                enhancement_applied=applied_enhancements,
                improvement_score=improvement_score,
                processing_time=processing_time,
                metadata={
                    "original_duration": len(audio_data) / sample_rate,
                    "enhanced_duration": len(enhanced_audio) / sample_rate,
                    "sample_rate": sample_rate
                }
            )
            
        except Exception as e:
            self.logger.error(f"Error enhancing audio: {str(e)}")
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            
            return AudioEnhancementResult(
                original_audio_path=audio_file_path,
                enhanced_audio_path="",
                enhancement_applied=[],
                improvement_score=0.0,
                processing_time=processing_time,
                metadata={"error": str(e)}
            )
    
    def _validate_audio_file(self, audio_file_path: str) -> bool:
        """Validate audio file exists and has supported format"""
        if not os.path.exists(audio_file_path):
            return False
        
        file_ext = os.path.splitext(audio_file_path)[1].lower()
        return file_ext in self.supported_formats
    
    async def _load_audio(self, audio_file_path: str) -> tuple:
        """Load audio file"""
        try:
            audio_data, sample_rate = librosa.load(audio_file_path, sr=None)
            return audio_data, sample_rate
        except Exception as e:
            self.logger.error(f"Error loading audio file {audio_file_path}: {str(e)}")
            raise
    
    async def _save_enhanced_audio(
        self, 
        audio_data: np.ndarray, 
        sample_rate: int, 
        original_path: str
    ) -> str:
        """Save enhanced audio to file"""
        try:
            # Create output file path
            base_name = os.path.splitext(os.path.basename(original_path))[0]
            output_path = tempfile.mktemp(suffix=f'_enhanced_{base_name}.wav')
            
            # Save audio
            sf.write(output_path, audio_data, sample_rate)
            
            self.logger.info(f"Enhanced audio saved to: {output_path}")
            return output_path
            
        except Exception as e:
            self.logger.error(f"Error saving enhanced audio: {str(e)}")
            raise
    
    async def _normalize_audio(self, audio_data: np.ndarray, sample_rate: int) -> np.ndarray:
        """Normalize audio levels"""
        try:
            # Convert to AudioSegment for normalization
            temp_path = tempfile.mktemp(suffix='.wav')
            sf.write(temp_path, audio_data, sample_rate)
            
            audio_segment = AudioSegment.from_wav(temp_path)
            normalized_audio = normalize(audio_segment)
            
            # Convert back to numpy array
            normalized_array = np.array(normalized_audio.get_array_of_samples())
            
            # Clean up temp file
            os.remove(temp_path)
            
            return normalized_array
            
        except Exception as e:
            self.logger.error(f"Error normalizing audio: {str(e)}")
            return audio_data
    
    async def _reduce_noise(self, audio_data: np.ndarray, sample_rate: int) -> np.ndarray:
        """Reduce background noise using spectral gating"""
        try:
            # Calculate noise profile from first 2 seconds
            noise_samples = int(2 * sample_rate)
            noise_profile = audio_data[:min(noise_samples, len(audio_data))]
            
            # Calculate noise spectrum
            noise_spectrum = np.abs(np.fft.fft(noise_profile))
            noise_threshold = np.mean(noise_spectrum) * 2.0
            
            # Apply spectral gating
            enhanced_audio = audio_data.copy()
            
            # Process in chunks to avoid memory issues
            chunk_size = int(0.5 * sample_rate)  # 0.5 second chunks
            for i in range(0, len(audio_data), chunk_size):
                chunk = audio_data[i:i + chunk_size]
                if len(chunk) < chunk_size:
                    # Pad last chunk if needed
                    chunk = np.pad(chunk, (0, chunk_size - len(chunk)))
                
                # Apply FFT
                spectrum = np.fft.fft(chunk)
                
                # Apply noise gate
                magnitude = np.abs(spectrum)
                phase = np.angle(spectrum)
                
                # Gate based on noise threshold
                gated_magnitude = np.where(magnitude > noise_threshold, magnitude, magnitude * 0.1)
                
                # Reconstruct signal
                gated_spectrum = gated_magnitude * np.exp(1j * phase)
                gated_chunk = np.real(np.fft.ifft(gated_spectrum))
                
                # Store result
                enhanced_audio[i:i + len(chunk)] = gated_chunk[:len(audio_data[i:i + chunk_size])]
            
            return enhanced_audio
            
        except Exception as e:
            self.logger.error(f"Error reducing noise: {str(e)}")
            return audio_data
    
    async def _apply_filters(self, audio_data: np.ndarray, sample_rate: int) -> np.ndarray:
        """Apply audio filters for enhancement"""
        try:
            # High-pass filter to remove low-frequency noise
            high_pass_cutoff = 80  # Hz
            high_pass_filter = librosa.effects.high_pass_filter(
                audio_data, sr=sample_rate, cutoff=high_pass_cutoff
            )
            
            # Low-pass filter to remove high-frequency noise
            low_pass_cutoff = 8000  # Hz
            low_pass_filter = librosa.effects.low_pass_filter(
                high_pass_filter, sr=sample_rate, cutoff=low_pass_cutoff
            )
            
            return low_pass_filter
            
        except Exception as e:
            self.logger.error(f"Error applying filters: {str(e)}")
            return audio_data
    
    async def _apply_compression(self, audio_data: np.ndarray, sample_rate: int) -> np.ndarray:
        """Apply dynamic range compression"""
        try:
            # Simple compression implementation
            threshold = 0.5
            ratio = 4.0
            
            compressed_audio = audio_data.copy()
            
            # Apply compression to samples above threshold
            above_threshold = np.abs(compressed_audio) > threshold
            compressed_audio[above_threshold] = np.sign(compressed_audio[above_threshold]) * (
                threshold + (np.abs(compressed_audio[above_threshold]) - threshold) / ratio
            )
            
            return compressed_audio
            
        except Exception as e:
            self.logger.error(f"Error applying compression: {str(e)}")
            return audio_data
    
    async def _calculate_improvement_score(
        self, 
        original_audio: np.ndarray, 
        enhanced_audio: np.ndarray
    ) -> float:
        """Calculate improvement score based on audio quality metrics"""
        try:
            # Calculate signal-to-noise ratio improvement
            original_snr = self._calculate_snr(original_audio)
            enhanced_snr = self._calculate_snr(enhanced_audio)
            snr_improvement = max(0, (enhanced_snr - original_snr) / max(original_snr, 1))
            
            # Calculate dynamic range improvement
            original_dynamic_range = np.max(original_audio) - np.min(original_audio)
            enhanced_dynamic_range = np.max(enhanced_audio) - np.min(enhanced_audio)
            dynamic_range_improvement = max(0, (enhanced_dynamic_range - original_dynamic_range) / max(original_dynamic_range, 1))
            
            # Calculate overall improvement score
            improvement_score = (snr_improvement + dynamic_range_improvement) / 2
            improvement_score = min(1.0, max(0.0, improvement_score))
            
            return improvement_score
            
        except Exception as e:
            self.logger.error(f"Error calculating improvement score: {str(e)}")
            return 0.0
    
    def _calculate_snr(self, audio_data: np.ndarray) -> float:
        """Calculate signal-to-noise ratio"""
        try:
            signal_power = np.mean(audio_data ** 2)
            noise_floor = np.percentile(audio_data ** 2, 10)
            snr = 10 * np.log10(signal_power / (noise_floor + 1e-10))
            return float(snr)
        except Exception:
            return 0.0
    
    async def batch_enhance_audio(
        self, 
        audio_files: List[str],
        enhancement_methods: Optional[List[str]] = None
    ) -> List[AudioEnhancementResult]:
        """
        Enhance multiple audio files in batch
        
        Args:
            audio_files: List of audio file paths
            enhancement_methods: List of enhancement methods to apply
            
        Returns:
            List of AudioEnhancementResult objects
        """
        results = []
        
        for audio_file in audio_files:
            try:
                result = await self.enhance_audio(audio_file, enhancement_methods)
                results.append(result)
            except Exception as e:
                self.logger.error(f"Error enhancing {audio_file}: {str(e)}")
                # Add error result
                results.append(AudioEnhancementResult(
                    original_audio_path=audio_file,
                    enhanced_audio_path="",
                    enhancement_applied=[],
                    improvement_score=0.0,
                    processing_time=0.0,
                    metadata={"error": str(e)}
                ))
        
        return results 