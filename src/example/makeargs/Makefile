# Defaults
CFLAGS ?= -O3 -g -ggdb
LDFLAGS ?=

BASIC_CFLAGS = -Wall -Wextra -fPIC
BASIC_LDFLAGS = -lm

# We use ALL_* variants
ALL_CFLAGS = $(BASIC_CFLAGS) $(CFLAGS)
ALL_LDFLAGS = $(BASIC_LDFLAGS) $(LDFLAGS)

LIBNAME=libmakeargs

DYLIBSUFFIX=so
STLIBSUFFIX=a
DYLIBNAME=$(LIBNAME).$(DYLIBSUFFIX)
DYLIB_MAKE_CMD=$(CC) -shared -o $(DYLIBNAME) $(ALL_LDFLAGS)
STLIBNAME=$(LIBNAME).$(STLIBSUFFIX)
STLIB_MAKE_CMD=ar rcs $(STLIBNAME)

# Platform-specific overrides
uname_S := $(shell sh -c 'uname -s 2>/dev/null || echo not')
ifeq ($(uname_S),xguo2)
DYLIBSUFFIX=dylib
DYLIB_MAKE_CMD=$(CC) -shared -o $(DYLIBNAME) $(ALL_LDFLAGS)
endif

all: $(DYLIBNAME) $(STLIBNAME)

OBJS += makeargs.o
OBJS += test_makeargs.o

$(OBJS): %.o: %.cpp
	$(CC) -o $*.o -c $(ALL_CFLAGS) $<

$(DYLIBNAME): makeargs.o
	$(DYLIB_MAKE_CMD) $^

$(STLIBNAME): makeargs.o
	$(STLIB_MAKE_CMD) $^

test_makeargs: $(OBJS)
	$(CC) $(ALL_CFLAGS) -o $@ $^ $(ALL_LDFLAGS)

clean:
	rm -rf test_makeargs
	rm -rf *.[ao]
