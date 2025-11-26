# Color Science Package Design

## Overview

The `color_science` package provides comprehensive spectral color calculations, including SPD-to-color space conversions, chromatic adaptation, and color space transformations. It handles the complexity of different spectral resolutions between device measurements and reference data.

## Package Structure

```
color_science/
├── __init__.py           # Package exports
├── color_science.py      # ColorScience, ColorScienceBase, SpectrumDataLoader
├── white_points.py       # WhitePoint - Standard illuminants
├── DESIGN.md            # This document
└── COLOUR_INTEGRATION.md # Integration guide for colour-science library
```

## Dependencies

**External Dependencies:**
- `numpy` - Numerical computations and array operations
- `colour-science` - Comprehensive color science library (core dependency)
  - Spectral data (CMF, illuminants)
  - Color space conversions
  - Chromatic adaptation
  - Spectral processing

**Internal Dependencies:**
- None - All spectral data comes from colour-science library

## Core Classes

### ColorScienceBase (Abstract Base Class)
**Purpose**: Define interface for color science implementations

**Interface:**
```python
class ColorScienceBase(ABC):
    @abstractmethod
    def spectrum_to_xyz(self, spd, wavelengths=None, illuminant="D65/10") -> Tuple[float, float, float]
    @abstractmethod
    def adapt_xyz(self, X, Y, Z, Ws, Wd, method="bradford") -> Tuple[float, float, float]
    @abstractmethod
    def xyz_to_lab(self, X, Y, Z, whitepoint=WhitePoint().D65_10) -> Tuple[float, float, float]
    @abstractmethod
    def xyz_to_rgb(self, X, Y, Z, out_255=True) -> Tuple[float, float, float]
    @abstractmethod
    def lab_to_xyz(self, L, a, b, whitepoint=WhitePoint().D65_10) -> Tuple[float, float, float]
    @abstractmethod
    def rgb_to_xyz(self, r, g, b) -> Tuple[float, float, float]
```

### SpectrumDataLoader
**Purpose**: Loads and manages CIE observer and illuminant spectral datasets using colour-science

**Key Responsibilities:**
- Access colour-science's built-in spectral data (CMF, illuminants)
- Handle wavelength interpolation using colour-science's SpectralDistribution
- Manage loaded datasets in memory
- Provide interface compatible with existing code

**Interface:**
```python
class SpectrumDataLoader:
    def __init__(self, wavelengths=None)
    
    def get_observer(self, wavelengths=None, observer="10") -> Dict[str, np.ndarray]
    def get_illuminant(self, wavelengths=None, illuminant="D65") -> Dict[str, np.ndarray]
```

**Implementation Notes:**
- Uses `colour.colorimetry.MSDS_CMFS` for Color Matching Functions
- Uses `colour.colorimetry.SDS_ILLUMINANTS` for standard illuminants
- All spectral data comes from colour-science library (no CSV files needed)
- Interpolation handled automatically by colour-science's SpectralDistribution

### ColorScience
**Purpose**: Concrete implementation of color science calculations

**Key Responsibilities:**
- Perform SPD-to-XYZ conversions
- Implement chromatic adaptation
- Convert between color spaces
- Handle spectral interpolation and resampling

**Interface:**
```python
class ColorScience(ColorScienceBase):
    def __init__(self, wavelengths=None, load=True)
    
    # Core conversion methods
    def spectrum_to_xyz(self, spd, wavelengths=None, illuminant="D65/10") -> Tuple[float, float, float]
    def xyz_to_lab(self, X, Y, Z, illuminant=WhitePoint.D65_10) -> Tuple[float, float, float]
    def xyz_to_rgb(self, X, Y, Z, out_255=True) -> Tuple[float, float, float]
    def lab_to_xyz(self, L, a, b, illuminant=WhitePoint.D65_10) -> Tuple[float, float, float]
    def rgb_to_xyz(self, r, g, b) -> Tuple[float, float, float]
    
    # Chromatic adaptation
    def adapt_xyz(self, X, Y, Z, Ws, Wd, method="bradford") -> Tuple[float, float, float]
    
    # Utility methods
    def upsample_interpolate(self, X, Xp, Yp) -> np.ndarray
```

### WhitePoint
**Purpose**: Standard CIE white points and illuminants

**Interface:**
```python
class WhitePoint:
    # Standard white points
    D65_2 = (0.95047, 1.00000, 1.08883)
    D65_10 = (0.94811, 1.00000, 1.07304)
    D50_2 = (0.96422, 1.00000, 0.82521)
    D50_10 = (0.96720, 1.00000, 0.81427)
    
    @staticmethod
    def get_available_white_points() -> Dict[str, Tuple[float, float, float]]
    @staticmethod
    def get_white_point(name: str) -> Tuple[float, float, float]
```

## Design Patterns

### Spectral Resolution Handling
- **Problem**: Device measures at 10nm intervals, reference data at 1nm
- **Solution**: Interpolation and resampling using scipy
- **Implementation**: `interpolate_spectrum()` method

### Data Loading Strategy
- **Separation of Concerns**: Spectrum datasets loading is handled by `SpectrumDataLoader` class
- **colour-science Integration**: All spectral data comes from colour-science library
- **No CSV Files**: Eliminates need for maintaining CSV files
- **Automatic Interpolation**: colour-science handles wavelength interpolation automatically
- **Comprehensive Data**: Access to many more illuminants and observers than before

### Color Space Conversions
- **XYZ as Intermediate**: All conversions go through XYZ
- **Illuminant Awareness**: Proper handling of different illuminants
- **Chromatic Adaptation**: Bradford transform for illuminant changes

## Key Algorithms

### SPD to XYZ Conversion
1. Use `SpectrumDataLoader` to get CIE observer data (2° or 10°) from colour-science
2. Use `SpectrumDataLoader` to get illuminant spectral data from colour-science
3. Create `SpectralDistribution` objects for SPD and illuminant
4. Use `colour.colorimetry.spectral_to_XYZ()` for conversion
5. Returns XYZ tristimulus values

### Chromatic Adaptation
1. Use `colour.adaptation.chromatic_adaptation_VonKries()` function
2. Supports Bradford, CAT02, and Von Kries transforms
3. Converts between illuminants using proven algorithms

### Color Space Conversions
- XYZ ↔ LAB: Using `colour.XYZ_to_Lab()` and `colour.Lab_to_XYZ()` with illuminant-specific white points
- XYZ ↔ RGB: Using `colour.XYZ_to_RGB()` and `colour.RGB_to_XYZ()` for sRGB
- RGB ↔ LAB: Via XYZ intermediate (using colour-science functions)

## Open Questions

1. **Observer Selection**: Should the application automatically choose 2° vs 10° observer based on measurement conditions?
   1. Default is 10°, D65
   2. User can chose different observer and/or illuminant

2. **Illuminant Database**: How should we handle the growing database of illuminants and make them easily discoverable?
   1. Should be a separate class that manages this data (move it out of color science)

3. **Precision vs Performance**: What precision should be maintained in calculations vs computational speed?
   1. Maximum precision preferred

4. **Custom Observers**: Should users be able to load custom observer data for specialized applications?
   1. Yes

5. **Spectral Range**: How should we handle measurements outside the standard 380-780nm range?
   1. This is CMF and illuminant spectrum dependent. 
   2. Perform calculations on matched wavelengths - missing wavelengths are 0 (not included at all)
   3. If user provides broader spd with matching cmf/illuminant - it is fine
   4. don't handle it explicitly

6. **Interpolation Methods**: Should we support different interpolation methods (linear, cubic, spline) for spectral data?
   1. Only spline

7. **Color Space Support**: Should we add support for additional color spaces (LUV, Hunter Lab, etc.)?
   1. Yes

8. **Validation**: What validation should be performed on input spectral data?
   1. Check if values make sense - fail if they don't
   2. Check if wavelength interval is consistent - issue a warning

9.  **Error Propagation**: How should we handle and report errors in color calculations?
    1.  let caller code catch exceptions

10. **Reference Data Updates**: How should we handle updates to CIE reference data?
    1.  whatever is in csv files is the truth

