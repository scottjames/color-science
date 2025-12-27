"""
Color Science Implementation

Comprehensive spectral color calculator using colour-science library.
Handles different resolutions between device (10nm) and reference data (1nm).
"""

import numpy as np
from abc import ABC, abstractmethod
from typing import Tuple, Optional, Dict, Any
import colour
from colour.colorimetry import (
    MSDS_CMFS,
    SDS_ILLUMINANTS,
    #spectral_to_XYZ,
    sd_to_XYZ,
    SpectralDistribution,
)
from colour import XYZ_to_Lab, Lab_to_XYZ, XYZ_to_RGB, RGB_to_XYZ
from colour.adaptation import chromatic_adaptation_VonKries
from .white_points import WhitePoint


class SpectrumDataLoader:
    """Loads and manages CIE observer and illuminant spectral datasets using colour-science."""
    
    def __init__(self, wavelengths=None):
        """Initialize the data loader with optional target wavelengths."""
        self.wavelengths = wavelengths
        self._observers = {
            '2': MSDS_CMFS['CIE 1931 2 Degree Standard Observer'],
            '10': MSDS_CMFS['CIE 1964 10 Degree Standard Observer'],
        }
        # Map common illuminant names
        self._illuminants = {
            'D65': SDS_ILLUMINANTS['D65'],
            'D50': SDS_ILLUMINANTS['D50'],
            'D55': SDS_ILLUMINANTS['D55'],
            'D75': SDS_ILLUMINANTS['D75'],
            'A': SDS_ILLUMINANTS['A'],
            'B': SDS_ILLUMINANTS['B'] if 'B' in SDS_ILLUMINANTS else None,
            'C': SDS_ILLUMINANTS['C'] if 'C' in SDS_ILLUMINANTS else None,
            'E': SDS_ILLUMINANTS['E'] if 'E' in SDS_ILLUMINANTS else None,
            # F-series illuminants
            'F1': SDS_ILLUMINANTS.get('F1'),
            'F2': SDS_ILLUMINANTS.get('F2'),
            'F3': SDS_ILLUMINANTS.get('F3'),
            'F4': SDS_ILLUMINANTS.get('F4'),
            'F5': SDS_ILLUMINANTS.get('F5'),
            'F6': SDS_ILLUMINANTS.get('F6'),
            'F7': SDS_ILLUMINANTS.get('F7'),
            'F8': SDS_ILLUMINANTS.get('F8'),
            'F9': SDS_ILLUMINANTS.get('F9'),
            'F10': SDS_ILLUMINANTS.get('F10'),
            'F11': SDS_ILLUMINANTS.get('F11'),
            'F12': SDS_ILLUMINANTS.get('F12'),
        }
        # Remove None values
        self._illuminants = {k: v for k, v in self._illuminants.items() if v is not None}
    
    def get_observer(self, wavelengths=None, observer="10"):
        """Get color matching function data from colour-science.
        
        Args:
            wavelengths: Optional wavelength array to interpolate to
            observer: Observer type ('2', '10', 'D65/10' format, etc.)
            
        Returns:
            dict with 'wavelengths', 'x_bar', 'y_bar', 'z_bar' arrays
        """
        # Parse observer (e.g., "D65/10" -> "10", "10" -> "10")
        if '/' in str(observer):
            observer = str(observer).split('/')[1]
        elif observer is None:
            observer = '10'
        
        observer = str(observer)
        if observer not in self._observers:
            raise ValueError(f"Unknown observer '{observer}'. Use '2' or '10'.")
        
        cmf = self._observers[observer]
        
        # If wavelengths specified, interpolate
        if wavelengths is not None:
            wavelengths = np.array(wavelengths)
            cmf_interp = cmf.interpolate(wavelengths)
            return {
                'wavelengths': cmf_interp.wavelengths,
                'x_bar': cmf_interp.values[..., 0],
                'y_bar': cmf_interp.values[..., 1],
                'z_bar': cmf_interp.values[..., 2],
            }
        
        # Return full CMF data
        return {
            'wavelengths': cmf.wavelengths,
            'x_bar': cmf.values[..., 0],
            'y_bar': cmf.values[..., 1],
            'z_bar': cmf.values[..., 2],
        }
    
    def get_illuminant(self, wavelengths=None, illuminant="D65"):
        """Get illuminant spectral data from colour-science.
        
        Args:
            wavelengths: Optional wavelength array to interpolate to
            illuminant: Illuminant name (e.g., 'D65', 'D50', 'A')
            
        Returns:
            dict with 'wavelengths' and 'values' arrays
        """
        # Parse illuminant (e.g., "D65/10" -> "D65")
        if '/' in str(illuminant):
            illuminant = str(illuminant).split('/')[0]
        elif illuminant is None:
            illuminant = 'D65'
        
        illuminant = str(illuminant).upper()
        if illuminant not in self._illuminants:
            available = ', '.join(sorted(self._illuminants.keys()))
            raise ValueError(f"Unknown illuminant '{illuminant}'. Available: {available}")
        
        spd = self._illuminants[illuminant]
        
        # If wavelengths specified, interpolate
        if wavelengths is not None:
            wavelengths = np.array(wavelengths)
            spd_interp = spd.interpolate(wavelengths)
            return {
                'wavelengths': spd_interp.wavelengths,
                'values': spd_interp.values,
            }
        
        # Return full illuminant data
        return {
            'wavelengths': spd.wavelengths,
            'values': spd.values,
        }


class ColorScienceBase(ABC):
    """Abstract base class for color science calculations."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @abstractmethod
    def spectrum_to_xyz(self, spd, wavelengths=None, illuminant="D65/10"):
        """Convert spectral power distribution to XYZ."""
        pass
    
    @abstractmethod
    def adapt_xyz(self, X, Y, Z, Ws, Wd, method="bradford"):
        """Chromatic adaptation of XYZ values."""
        pass
    
    @abstractmethod
    def xyz_to_lab(self, X, Y, Z, illuminant=WhitePoint.D65_10):
        """Convert XYZ to LAB color space."""
        pass
    
    @abstractmethod
    def xyz_to_rgb(self, X, Y, Z, out_255=True):
        """Convert XYZ to RGB."""
        pass
    
    @abstractmethod
    def lab_to_xyz(self, L, a, b, illuminant=WhitePoint.D65_10):
        """Convert LAB to XYZ color space."""
        pass
    
    @abstractmethod
    def rgb_to_xyz(self, r, g, b):
        """Convert RGB to XYZ."""
        pass

    def rgb_to_lab(self, r, g, b, illuminant=None):
        """Convert sRGB → CIE LAB by chaining rgb_to_xyz → xyz_to_lab."""
        X, Y, Z = self.rgb_to_xyz(r, g, b)
        L, a, b = self.xyz_to_lab(X, Y, Z, illuminant=illuminant)
        return L, a, b

    def lab_to_rgb(self, L, a, b, illuminant=None, out_255=True):
        """Convert CIE LAB → sRGB by chaining lab_to_xyz → xyz_to_rgb."""
        X, Y, Z = self.lab_to_xyz(L, a, b, illuminant=illuminant)
        r, g, b = self.xyz_to_rgb(X, Y, Z, out_255=out_255)
        return r, g, b

    def calculate_k_s(self, reflectance):
        """Calculate Kubelka-Munk function from reflectance."""
        R = np.array(reflectance) / 100.0  # Convert to 0-1 range
        # Avoid division by zero
        R = np.clip(R, 0.01, 0.99)
        k_s = (1 - R)**2 / (2 * R)
        return k_s


class ColorScience(ColorScienceBase):
    """Comprehensive spectral color calculator using colour-science library."""
    
    def __init__(self, wavelengths=None, load=True):
        """Initialize ColorScience with optional wavelengths.
        
        Args:
            wavelengths: Optional wavelength array for device measurements
            load: Whether to preload reference data (for compatibility, does nothing now)
        """
        self.wavelengths = wavelengths
        self._data_loader = SpectrumDataLoader(wavelengths=wavelengths)
    
    def upsample_interpolate(self, X, Xp, Yp):
        """Interpolates low-resolution data (Xp, Yp) onto a new high-resolution X grid.
        
        Note: This method is kept for backward compatibility. colour-science's
        SpectralDistribution.interpolate() provides better functionality.
        """
        X  = np.array(X, dtype=float)
        Xp = np.array(Xp, dtype=float)
        Yp = np.array(Yp, dtype=float)
        Y = np.interp(X, Xp, Yp)
        return Y

    def spectrum_to_xyz(self, spd, wavelengths=None, illuminant="D65/10"):
        """Convert a spectral power distribution to CIE XYZ tristimulus values using colour-science.
        
        Args:
            spd: Spectral power distribution (array of values)
            wavelengths: Wavelength array (if None, uses self.wavelengths)
            illuminant: Illuminant name (e.g., "D65/10", "D50/2")
            
        Returns:
            Tuple of (X, Y, Z) tristimulus values
        """
        # Use instance wavelengths if not provided
        if wavelengths is None:
            if self.wavelengths is None:
                raise ValueError("wavelengths must be provided if not set in constructor")
            wavelengths = np.array(self.wavelengths)
        else:
            wavelengths = np.array(wavelengths)
        
        spd = np.array(spd)
        
        if len(wavelengths) != len(spd):
            raise ValueError(f"wavelengths ({len(wavelengths)}) and spd ({len(spd)}) lengths must match")
        
        # Parse illuminant (e.g., "D65/10" -> illuminant="D65", observer="10")
        if illuminant is None:
            # Emissive spectrum (no illuminant)
            observer_str = '10'
            illum_sd = None
        elif '/' in str(illuminant):
            illum_name, observer_str = str(illuminant).split('/')
            # Get illuminant from colour-science
            illum = self._data_loader.get_illuminant(wavelengths, illum_name)
            # Create illuminant SpectralDistribution
            illum_sd = SpectralDistribution(illum['values'], illum['wavelengths'])
        else:
            # Default to 10 degree observer if not specified
            illum_name = str(illuminant).upper()
            observer_str = '10'
            # Get illuminant from colour-science
            illum = self._data_loader.get_illuminant(wavelengths, illum_name)
            # Create illuminant SpectralDistribution
            illum_sd = SpectralDistribution(illum['values'], illum['wavelengths'])
        
        # Get CMF matching the observer
        cmf_name = 'CIE 1964 10 Degree Standard Observer' if observer_str == '10' else 'CIE 1931 2 Degree Standard Observer'
        cmf = MSDS_CMFS[cmf_name]
        
        # Create SpectralDistribution from spd
        spd_sd = SpectralDistribution(spd, wavelengths)
        
        # Use colour-science function for conversion
        if illum_sd is None:
            # Emissive spectrum (no illuminant)
            XYZ = spectral_to_XYZ(
                spd_sd,
                cmfs=cmf
            )
        else:
            # Reflective spectrum (with illuminant)
            XYZ = spectral_to_XYZ(
                spd_sd,
                illuminant=illum_sd,
                cmfs=cmf
            )
        
        return float(XYZ[0]), float(XYZ[1]), float(XYZ[2])

    def adapt_xyz(self, X, Y, Z, Ws, Wd, method="bradford"):
        """Adapt XYZ from source white Ws to destination white Wd using colour-science.
        
        Args:
            X, Y, Z: Source XYZ values
            Ws: Source white point (X, Y, Z tuple)
            Wd: Destination white point (X, Y, Z tuple)
            method: Adaptation method ('bradford', 'cat02', 'von_kries')
            
        Returns:
            Tuple of adapted (X, Y, Z) values
        """
        XYZ = np.array([X, Y, Z])
        Ws = np.array(Ws)
        Wd = np.array(Wd)
        
        # Map method names to colour-science transform names
        method_map = {
            'bradford': 'Bradford',
            'cat02': 'CAT02',
            'kries': 'Von Kries',
            'von_kries': 'Von Kries',
        }
        
        colour_method = method_map.get(method.lower())
        if colour_method is None:
            raise ValueError(f"Unknown adaptation method '{method}'. "
                            f"Use one of: {', '.join(method_map.keys())}")
        
        # Use colour-science chromatic adaptation
        XYZ_adapted = chromatic_adaptation_VonKries(
            XYZ,
            Ws,
            Wd,
            transform=colour_method
        )
        
        return float(XYZ_adapted[0]), float(XYZ_adapted[1]), float(XYZ_adapted[2])

    def xyz_to_lab(self, X, Y, Z, illuminant=WhitePoint.D65_10):
        """Convert CIE XYZ to CIE LAB color space using colour-science.
        
        Args:
            X, Y, Z: XYZ tristimulus values
            illuminant: Reference white point (X, Y, Z tuple) or WhitePoint constant
            
        Returns:
            Tuple of (L, a, b) values
        """
        if illuminant is None:
            illuminant = WhitePoint.D65_10
        
        if isinstance(illuminant, (tuple, list)):
            XYZ_n = np.array(illuminant)
        else:
            raise ValueError("illuminant must be a tuple of (Xn, Yn, Zn)")
        
        XYZ = np.array([X, Y, Z])
        
        # Use colour-science function
        Lab = XYZ_to_Lab(XYZ, illuminant=XYZ_n)
        
        return float(Lab[0]), float(Lab[1]), float(Lab[2])

    def xyz_to_rgb(self, X, Y, Z, out_255=True):
        """Convert CIE XYZ (D65) to sRGB using colour-science.
        
        Args:
            X, Y, Z: XYZ tristimulus values
            out_255: If True, return values 0-255; if False, return 0-1
            
        Returns:
            Tuple of (r, g, b) values
        """
        XYZ = np.array([X, Y, Z])
        
        # Use colour-science function for sRGB
        RGB = XYZ_to_RGB(
            XYZ,
            illuminant=WhitePoint.D65_10,
            method='sRGB'
        )
        
        # Clip to valid range
        RGB = np.clip(RGB, 0, 1)
        
        if out_255:
            RGB = (RGB * 255).round().astype(int)
        
        return tuple(float(i) for i in RGB)

    def lab_to_xyz(self, L, a, b, illuminant=WhitePoint.D65_10):
        """Convert CIE LAB to CIE XYZ color space using colour-science.
        
        Args:
            L, a, b: LAB color values
            illuminant: Reference white point (X, Y, Z tuple) or WhitePoint constant
            
        Returns:
            Tuple of (X, Y, Z) values
        """
        if illuminant is None:
            illuminant = WhitePoint.D65_10
        
        if isinstance(illuminant, (tuple, list)):
            XYZ_n = np.array(illuminant)
        else:
            raise ValueError("illuminant must be a tuple of (Xn, Yn, Zn)")
        
        Lab = np.array([L, a, b])
        
        # Use colour-science function
        XYZ = Lab_to_XYZ(Lab, illuminant=XYZ_n)
        
        return float(XYZ[0]), float(XYZ[1]), float(XYZ[2])

    def rgb_to_xyz(self, r, g, b):
        """Convert sRGB (0–255 or 0–1) to CIE XYZ (D65) using colour-science.
        
        Args:
            r, g, b: RGB color values (0-255 or 0-1)
            
        Returns:
            Tuple of (X, Y, Z) values
        """
        RGB = np.array([r, g, b], dtype=float)
        
        # Normalize to 0-1 if needed
        if RGB.max() > 1.0:
            RGB /= 255.0
        
        RGB = np.clip(RGB, 0, 1)
        
        # Use colour-science function for sRGB
        XYZ = RGB_to_XYZ(
            RGB,
            illuminant=WhitePoint.D65_10,
            method='sRGB'
        )
        
        return float(XYZ[0]), float(XYZ[1]), float(XYZ[2])
