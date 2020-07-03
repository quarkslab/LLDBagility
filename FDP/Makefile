.PHONY: fdp virtualbox

fdp:
	# Build the static and shared FDP libraries and the FDP test executables
ifeq ($(wildcard build/.),)
	mkdir build
	cd build/ &&\
		cmake ..
endif
	cd build/ &&\
		make

	# Generate the PyFDP distribution wheel
	cp build/lib/libFDP.dylib PyFDP/PyFDP/
	cd PyFDP/ &&\
		python3 setup.py bdist_wheel

	# Collect files for distribution
	mkdir -p out-latest/include/FDP
	cp -r FDP/include/ out-latest/include/FDP
	cp build/lib/libFDP.a out-latest/
	cp build/lib/libFDP.dylib out-latest/
	cp build/bin/testFDP out-latest/
	cp build/bin/testFDPClientServer out-latest/
	cp build/bin/testFDPClientServer out-latest/
	cp PyFDP/dist/PyFDP-*-py3-none-any.whl out-latest/

	# Clean-up
	rm -r PyFDP/PyFDP.egg-info/
	rm -r PyFDP/PyFDP/libFDP.dylib
	rm -r PyFDP/build/
	rm -r PyFDP/dist/

virtualbox: fdp
ifeq ($(wildcard virtualbox/build/env.sh),)
	mkdir -p virtualbox/build
	cd virtualbox/ &&\
		FDPINC="$(shell pwd)/out-latest/include"\
		FDPLIB="$(shell pwd)/out-latest"\
		"$(shell pwd)/virtualbox-build.py" "$(shell pwd)/virtualbox/build/"
endif
	cd virtualbox/ &&\
		source build/env.sh &&\
		FDPINC="$(shell pwd)/out-latest/include"\
		FDPLIB="$(shell pwd)/out-latest"\
		kmk
	rm -rf "$(shell pwd)/out-latest/VirtualBox"
	"$(shell pwd)/virtualbox-pack.py" "$(shell pwd)/virtualbox/build/" "$(shell pwd)/out-latest/VirtualBox" "$(shell pwd)/out-latest/libFDP.dylib"

clean:
	rm -rf build/
	rm -rf out-latest/
	rm -rf virtualbox/build/
