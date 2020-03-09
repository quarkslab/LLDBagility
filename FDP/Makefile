.PHONY: all clean

all:
	mkdir -p build

	# Build the FDP static and shared libraries and the FDP test executables
	cd build/ &&\
		cmake .. &&\
		make

	# Generate the PyFDP distribution wheel
	cp build/lib/libFDP.dylib PyFDP/PyFDP/
	cd PyFDP/ &&\
		python3 setup.py sdist bdist_wheel

clean:
	rm -rf build/
	rm -rf PyFDP/build/
	rm -rf PyFDP/dist/
	rm -rf PyFDP/PyFDP/libFDP.dylib
	rm -rf PyFDP/PyFDP.egg-info/
