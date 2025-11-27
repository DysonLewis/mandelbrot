PYTHON := python3
PYTHON_CONFIG := $(PYTHON)-config
PYTHON_INCLUDES := $(shell $(PYTHON_CONFIG) --includes)
PYTHON_LDFLAGS := $(shell $(PYTHON_CONFIG) --ldflags)
NUMPY_INCLUDE := $(shell $(PYTHON) -c "import numpy; print(numpy.get_include())")

CXX := g++
CXXFLAGS := -std=c++23 -O3 -fPIC -Wall $(PYTHON_INCLUDES) -I$(NUMPY_INCLUDE) -DNPY_NO_DEPRECATED_API=NPY_1_7_API_VERSION -DNPY_NO_DEPRECATED_API=NPY_1_7_API_VERSION
LDFLAGS := -shared $(PYTHON_LDFLAGS) -lpthread

TARGET := mandelbrot$(shell $(PYTHON_CONFIG) --extension-suffix)
SOURCE := mandelbrot.cpp

.PHONY: all clean

all: $(TARGET)

$(TARGET): $(SOURCE)
	$(CXX) $(CXXFLAGS) $(SOURCE) -o $(TARGET) $(LDFLAGS)

clean:
	rm -f $(TARGET) output.fits mandelbrot_color.png