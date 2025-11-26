# Colour-Science Library Integration

## Overview

The `colour-science` library (https://www.colour-science.org/) is a comprehensive Python package that provides:

- **Extensive spectral data**: Built-in CMF (Color Matching Functions), illuminants, and observer data
- **Color space conversions**: Many color space transformations (XYZ, LAB, LUV, RGB, etc.)
- **Chromatic adaptation**: Multiple adaptation methods (Bradford, von Kries, CAT02, etc.)
- **Spectral processing**: Built-in interpolation, resampling, and wavelength handling
- **Color appearance models**: CAM16, CIECAM02, etc.
- **Color difference metrics**: ΔE*00, ΔE*94, ΔE*76, etc.

## Current vs. Colour-Science Approach

### Current Implementation
- Loads CMF and illuminant data from CSV files
- Manual interpolation and resampling
- Custom color space conversions
- Manual spectral processing

### With Colour-Science
- Built-in spectral datasets (no CSV files needed)
- Built-in interpolation and resampling functions
- Extensive color space conversions
- Well-tested, validated algorithms

## Integration Strategy

### Option 1: Use Colour-Science as Backend (Recommended)
Replace CSV loading and core calculations with `colour-science` functions while maintaining the same interface.

**Benefits:**
- More comprehensive spectral data (no CSV maintenance)
- Well-tested algorithms
- Extended functionality available
- Less code to maintain

**Example:**
```python
import colour
from colour.colorimetry import (
    spectral_to_XYZ,
    MSDS_CMFS,
    SDS_ILLUMINANTS,
    handle_spectral_axes
)

# Instead of loading CSV files:
# cmf = load_csv("CIE_xyz_1964_10deg.csv")

# Use colour-science:
cmf = MSDS_CMFS['CIE 1964 10 Degree Standard Observer']
illuminant = SDS_ILLUMINANTS['D65']

# Convert SPD to XYZ
XYZ = spectral_to_XYZ(spd, illuminant, cmf)
```

### Option 2: Hybrid Approach
Use `colour-science` for data loading and spectral operations, keep custom color space conversions.

**Benefits:**
- Keep existing logic where it works
- Leverage extensive spectral data
- Gradual migration path

### Option 3: Wrapper Around Colour-Science
Wrap `colour-science` functions to match existing interface.

**Benefits:**
- Full compatibility with existing code
- Access to all colour-science features
- Can customize as needed

## Key Colour-Science Features to Use

### 1. Spectral Data
```python
from colour.colorimetry import (
    MSDS_CMFS,           # Color Matching Functions
    SDS_ILLUMINANTS,     # Standard Illuminants
    SDS_LIGHT_SOURCES,   # Light Sources
    SpectralDistribution,
    MultiSpectralDistributions
)

# Available CMFs:
cmf_2deg = MSDS_CMFS['CIE 1931 2 Degree Standard Observer']
cmf_10deg = MSDS_CMFS['CIE 1964 10 Degree Standard Observer']

# Available Illuminants:
d65 = SDS_ILLUMINANTS['D65']
d50 = SDS_ILLUMINANTS['D50']
a = SDS_ILLUMINANTS['A']
# Plus many more: D55, D75, F1-F12, LED spectra, etc.
```

### 2. Spectral to XYZ Conversion
```python
from colour.colorimetry import spectral_to_XYZ

# Convert SPD to XYZ
XYZ = spectral_to_XYZ(
    spd,                    # SpectralDistribution or array
    illuminant=d65,         # Illuminant SPD
    cmfs=cmf_10deg          # CMF data
)
```

### 3. Color Space Conversions
```python
from colour import XYZ_to_Lab, Lab_to_XYZ
from colour import XYZ_to_RGB, RGB_to_XYZ

# XYZ to LAB
Lab = XYZ_to_Lab(XYZ, illuminant=d65_white_point)

# LAB to XYZ
XYZ = Lab_to_XYZ(Lab, illuminant=d65_white_point)

# XYZ to RGB (sRGB)
RGB = XYZ_to_RGB(XYZ, illuminant=d65_white_point)
```

### 4. Chromatic Adaptation
```python
from colour.adaptation import chromatic_adaptation_VonKries

# Adapt XYZ from one illuminant to another
XYZ_adapted = chromatic_adaptation_VonKries(
    XYZ,
    source_illuminant=source_white_point,
    target_illuminant=target_white_point,
    transform='Bradford'
)
```

### 5. Spectral Interpolation
```python
from colour import SpectralDistribution
from colour.colorimetry import handle_spectral_axes

# Create SpectralDistribution and interpolate
spd = SpectralDistribution(spd_data, wavelengths)
spd_interpolated = spd.interpolate(
    np.arange(380, 781, 1)  # New wavelength range
)
```

## Proposed Refactoring

### Update SpectrumDataLoader to use Colour-Science

```python
import colour
from colour.colorimetry import MSDS_CMFS, SDS_ILLUMINANTS
from colour import SpectralDistribution

class SpectrumDataLoader:
    """Loads spectral data using colour-science library."""
    
    def __init__(self, wavelengths=None):
        self.wavelengths = wavelengths
        self._observers = {
            '2': MSDS_CMFS['CIE 1931 2 Degree Standard Observer'],
            '10': MSDS_CMFS['CIE 1964 10 Degree Standard Observer']
        }
        self._illuminants = {
            'D65': SDS_ILLUMINANTS['D65'],
            'D50': SDS_ILLUMINANTS['D50'],
            'A': SDS_ILLUMINANTS['A'],
            # Add more as needed
        }
    
    def get_observer(self, wavelengths=None, observer="10"):
        """Get CMF data from colour-science."""
        cmf = self._observers[observer]
        if wavelengths is not None:
            # Interpolate to desired wavelengths
            cmf_interp = cmf.interpolate(wavelengths)
            return {
                'wavelengths': cmf_interp.wavelengths,
                'x_bar': cmf_interp.values[:, 0],
                'y_bar': cmf_interp.values[:, 1],
                'z_bar': cmf_interp.values[:, 2]
            }
        return cmf
    
    def get_illuminant(self, wavelengths=None, illuminant="D65"):
        """Get illuminant from colour-science."""
        spd = self._illuminants[illuminant]
        if wavelengths is not None:
            spd = spd.interpolate(wavelengths)
        return spd
```

### Update ColorScience to use Colour-Science functions

```python
from colour.colorimetry import spectral_to_XYZ
from colour import XYZ_to_Lab, Lab_to_XYZ, XYZ_to_RGB

class ColorScience(ColorScienceBase):
    def spectrum_to_xyz(self, spd, wavelengths=None, illuminant="D65/10"):
        """Convert SPD to XYZ using colour-science."""
        # Parse illuminant (e.g., "D65/10")
        illum_name, observer = illuminant.split('/')
        
        # Get CMF and illuminant
        cmf = self._data_loader.get_observer(wavelengths, observer)
        illum = self._data_loader.get_illuminant(wavelengths, illum_name)
        
        # Create SpectralDistribution if needed
        if not isinstance(spd, SpectralDistribution):
            spd = SpectralDistribution(spd, wavelengths)
        
        # Use colour-science function
        XYZ = spectral_to_XYZ(spd, illuminant=illum, cmfs=cmf)
        return tuple(XYZ)
    
    def xyz_to_lab(self, X, Y, Z, illuminant=WhitePoint.D65_10):
        """Convert XYZ to LAB using colour-science."""
        XYZ = np.array([X, Y, Z])
        Lab = XYZ_to_Lab(XYZ, illuminant=illuminant)
        return tuple(Lab)
```

## Migration Path

1. **Phase 1**: Add colour-science as optional dependency, use it alongside CSV files
2. **Phase 2**: Replace CSV loading with colour-science data loading
3. **Phase 3**: Replace custom conversions with colour-science functions
4. **Phase 4**: Remove CSV files and custom implementations (keep as fallback)

## Benefits Summary

1. **No CSV maintenance**: All spectral data built-in
2. **More illuminants**: Access to many more standard illuminants
3. **Better tested**: Well-validated algorithms
4. **Extended functionality**: Color appearance models, color difference metrics
5. **Active development**: Regularly updated with latest CIE standards
6. **Documentation**: Comprehensive documentation and examples

## Compatibility

The integration can be done while maintaining the existing interface, so existing code continues to work unchanged.

