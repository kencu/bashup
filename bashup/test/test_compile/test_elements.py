import textwrap

from ...compile import elements
from ... import parse
from ... import test


#
# Tests
#

def test_compile_fn_spec_to_bash_without_args():
    expected = textwrap.dedent("""
        #
        # usage: hello [ARGS]
        #
        hello() {
    """).strip()

    actual = elements.compile_fn_spec_to_bash(fn_spec=parse.FnSpec(
        name='hello',
        args=()))

    test.assert_eq(actual, expected)


def test_compile_fn_spec_to_bash_with_args():
    expected = textwrap.dedent("""
        #
        # usage: enable_ramdisk --size=<SIZE> [--path=<PATH>] [ARGS]
        #
        enable_ramdisk() {
            local size
            local size__set=0
            local path='/ramdisk'
            local args=()

            while (( $# )); do
                if [[ "${1}" == --size=* ]]; then
                    size=${1#--size=}
                    size__set=1
                elif [[ "${1}" == --path=* ]]; then
                    path=${1#--path=}
                else
                    args+=("${1}")
                fi
                shift
            done

            if ! (( size__set )); then
                echo "[ERROR] The --size parameter must be given."
                return 1
            fi

            __enable_ramdisk "${size}" "${path}" "${args[@]}"
        }

        __enable_ramdisk() {
            local size=${1}
            local path=${2}
            shift 2
    """).lstrip()

    actual = elements.compile_fn_spec_to_bash(fn_spec=parse.FnSpec(
        name='enable_ramdisk',
        args=(parse.FnArgSpec(name='size', value=None),
              parse.FnArgSpec(name='path', value="'/ramdisk'"))))

    test.assert_eq(actual, expected)


def test_compile_fns_to_bash_single_fn_without_args():
    expected = textwrap.dedent("""
        #
        # usage: hello [ARGS]
        #
        hello() {
            echo "hello!"
        }
    """).strip()

    actual = elements.compile_fns_to_bash(bashup_str=textwrap.dedent("""
        @fn hello {
            echo "hello!"
        }
    """).strip())

    test.assert_eq(actual, expected)


def test_compile_fns_to_bash_multiple_fns_without_args():
    expected = textwrap.dedent("""
        #!/bin/bash

        set -e -o pipefail

        #
        # usage: hello [ARGS]
        #
        hello() { echo "hello!"; }

        hello

        #
        # usage: world [ARGS]
        #
        world() {
            echo "world!"
        }

        world
    """).strip()

    actual = elements.compile_fns_to_bash(bashup_str=textwrap.dedent("""
        #!/bin/bash

        set -e -o pipefail

        @fn hello { echo "hello!"; }

        hello

        @fn world {
            echo "world!"
        }

        world
    """).strip())

    test.assert_eq(actual, expected)


def test_compile_fns_to_bash_multiple_fns_with_args():
    expected = textwrap.dedent("""
        #!/bin/bash

        set -e -o pipefail

        #
        # usage: enable_ramdisk --size=<SIZE> [--path=<PATH>] [ARGS]
        #
        enable_ramdisk() {
            local size
            local size__set=0
            local path='/ramdisk'
            local args=()

            while (( $# )); do
                if [[ "${1}" == --size=* ]]; then
                    size=${1#--size=}
                    size__set=1
                elif [[ "${1}" == --path=* ]]; then
                    path=${1#--path=}
                else
                    args+=("${1}")
                fi
                shift
            done

            if ! (( size__set )); then
                echo "[ERROR] The --size parameter must be given."
                return 1
            fi

            __enable_ramdisk "${size}" "${path}" "${args[@]}"
        }

        __enable_ramdisk() {
            local size=${1}
            local path=${2}
            shift 2

            if ! grep "^tmpfs ${path}" /etc/fstab; then
                echo "tmpfs ${path} tmpfs rw,size=${size} 0 0" >> /etc/fstab
                mkdir -p "${path}"
                mount "${path}"
            fi
        }

        #
        # usage: ensure_root [ARGS]
        #
        ensure_root() {
            if [ ${EUID} -ne 0 ]; then
                echo "[ERROR] Script must be run as root."
                return 1
            fi
        }

        ensure_root
        enable_ramdisk --size="4G"
    """).strip()

    actual = elements.compile_fns_to_bash(bashup_str=textwrap.dedent("""
        #!/bin/bash

        set -e -o pipefail

        @fn enable_ramdisk size, path='/ramdisk' {
            if ! grep "^tmpfs ${path}" /etc/fstab; then
                echo "tmpfs ${path} tmpfs rw,size=${size} 0 0" >> /etc/fstab
                mkdir -p "${path}"
                mount "${path}"
            fi
        }

        @fn ensure_root {
            if [ ${EUID} -ne 0 ]; then
                echo "[ERROR] Script must be run as root."
                return 1
            fi
        }

        ensure_root
        enable_ramdisk --size="4G"
    """).strip())

    test.assert_eq(actual, expected)


def test_compile_fns_to_bash_custom_indents():
    expected = textwrap.dedent("""
        {
        \t#
        \t# usage: enable_ramdisk --size=<SIZE> [--path=<PATH>] [ARGS]
        \t#
        \tenable_ramdisk() {
        \t local size
        \t local size__set=0
        \t local path='/ramdisk'
        \t local args=()

        \t while (( $# )); do
        \t  if [[ "${1}" == --size=* ]]; then
        \t   size=${1#--size=}
        \t   size__set=1
        \t  elif [[ "${1}" == --path=* ]]; then
        \t   path=${1#--path=}
        \t  else
        \t   args+=("${1}")
        \t  fi
        \t  shift
        \t done

        \t if ! (( size__set )); then
        \t  echo "[ERROR] The --size parameter must be given."
        \t  return 1
        \t fi

        \t __enable_ramdisk "${size}" "${path}" "${args[@]}"
        \t}

        \t__enable_ramdisk() {
        \t local size=${1}
        \t local path=${2}
        \t shift 2

        \t if ! grep "^tmpfs ${path}" /etc/fstab; then
        \t  echo "tmpfs ${path} tmpfs rw,size=${size} 0 0" >> /etc/fstab
        \t  mkdir -p "${path}"
        \t  mount "${path}"
        \t fi
        \t}
        }

        {
            #
            # usage: ensure_root [ARGS]
            #
            ensure_root() {
            \tif [ ${EUID} -ne 0 ]; then
            \t\techo "[ERROR] Script must be run as root."
            \t\treturn 1
            \tfi
            }
        }
    """).strip()

    actual = elements.compile_fns_to_bash(bashup_str=textwrap.dedent("""
        {
        \t@fn enable_ramdisk size, path='/ramdisk' {
        \t if ! grep "^tmpfs ${path}" /etc/fstab; then
        \t  echo "tmpfs ${path} tmpfs rw,size=${size} 0 0" >> /etc/fstab
        \t  mkdir -p "${path}"
        \t  mount "${path}"
        \t fi
        \t}
        }

        {
            @fn ensure_root {
            \tif [ ${EUID} -ne 0 ]; then
            \t\techo "[ERROR] Script must be run as root."
            \t\treturn 1
            \tfi
            }
        }
    """).strip())

    test.assert_eq(actual, expected)


def test_compile_fns_to_bash_custom_indents_with_blank_lines():
    expected = textwrap.dedent("""
        {
        \t#
        \t# usage: enable_ramdisk --size=<SIZE> [--path=<PATH>] [ARGS]
        \t#
        \tenable_ramdisk() {
        \t local size
        \t local size__set=0
        \t local path='/ramdisk'
        \t local args=()

        \t while (( $# )); do
        \t  if [[ "${1}" == --size=* ]]; then
        \t   size=${1#--size=}
        \t   size__set=1
        \t  elif [[ "${1}" == --path=* ]]; then
        \t   path=${1#--path=}
        \t  else
        \t   args+=("${1}")
        \t  fi
        \t  shift
        \t done

        \t if ! (( size__set )); then
        \t  echo "[ERROR] The --size parameter must be given."
        \t  return 1
        \t fi

        \t __enable_ramdisk "${size}" "${path}" "${args[@]}"
        \t}

        \t__enable_ramdisk() {
        \t local size=${1}
        \t local path=${2}
        \t shift 2



        \t if ! grep "^tmpfs ${path}" /etc/fstab; then
        \t  echo "tmpfs ${path} tmpfs rw,size=${size} 0 0" >> /etc/fstab
        \t  mkdir -p "${path}"
        \t  mount "${path}"
        \t fi
        \t}
        }
    """).strip()

    actual = elements.compile_fns_to_bash(bashup_str=textwrap.dedent("""
        {
        \t@fn enable_ramdisk size, path='/ramdisk' {


        \t if ! grep "^tmpfs ${path}" /etc/fstab; then
        \t  echo "tmpfs ${path} tmpfs rw,size=${size} 0 0" >> /etc/fstab
        \t  mkdir -p "${path}"
        \t  mount "${path}"
        \t fi
        \t}
        }
    """).strip())

    test.assert_eq(actual, expected)


def test_compile_fns_to_bash_nested_fns():
    expected = textwrap.dedent("""
        #
        # usage: level_1 [ARGS]
        #
        level_1() {
            #
            # usage: level_2 [ARGS]
            #
            level_2() {
                #
                # usage: level_3 [ARGS]
                #
                level_3() {
                    :
                }
            }
        }
    """).strip()

    actual = elements.compile_fns_to_bash(bashup_str=textwrap.dedent("""
        @fn level_1 {
            @fn level_2 {
                @fn level_3 {
                    :
                }
            }
        }
    """).strip())

    test.assert_eq(actual, expected)
