#!/usr/bin/env python2

import os
import re
import sys
import logging
import argparse
import collections

from slpp import slpp as lua


class Default:
    DIR_HIGHLIGHT_THEMES = "/usr/share/highlight/themes"
    DIR_OUTPUT = "out"


class KakouneFace(object):
    BuiltinFaces = [
        "attribute",
        "block",
        "bold",
        "builtin",
        "bullet",
        "comment",
        "function",
        "header",
        "italic",
        "keyword",
        "link",
        "list",
        "meta",
        "module",
        "mono",
        "operator",
        "string",
        "title",
        "type",
        "value",
        "variable",
        "BufferPadding",
        "Default",
        "Error",
        "Information",
        "LineNumberCursor",
        "LineNumbers",
        "MatchingChar",
        "MenuBackground",
        "MenuForeground",
        "MenuInfo",
        "PrimaryCursor",
        "PrimaryCursorEol",
        "PrimarySelection",
        "Prompt",
        "SecondaryCursor",
        "SecondaryCursorEol",
        "SecondarySelection",
        "StatusCursor",
        "StatusLine",
        "StatusLineInfo",
        "StatusLineMode",
        "StatusLineValue",
    ]

    def __init__(self, name, color_fg, color_bg="default", bold=False, italic=False, underline=False):
        super(KakouneFace, self).__init__()

        assert(name in KakouneFace.BuiltinFaces)

        self.name = name
        self.color_bg = color_fg
        self.color_bg = color_bg
        self.bold = bold
        self.italic = italic
        self.underline = underline

    def __str__(self):
        s = self.color_fg

        if self.color_bg != "default":
            s += ",{0}".format(self.color_bg)

        has_attr = self.bold or self.italic or self.underline
        if has_attr:
            s += "+"

        if self.bold:
            s += "b"
        if self.italic:
            s += "i"
        if self.underline:
            s += "u"

        return s


def write_theme(path, name_theme, data):
    ## NOTE: some faces use previously declared faces to initialize their value,
    ## the following resolves them
    for face in ["Default", "Canvas", "Number", "Escape", "String", "PreProcessor", "StringPreProc", "BlockComment", "LineComment", "LineNum", "Operator"]:
        if face not in data:
            continue

        if isinstance(data[face], str):
            data[face] = data[data[face]]

    description    = data["Description"]   # Defines theme description
    default        = data["Default"]       # Colour of unspecified text
    canvas         = data["Canvas"]        # Background colour
    number         = data["Number"]        # Formatting of numbers
    escape         = data["Escape"]        # Formatting of escape sequences
    string         = data["String"]        # Formatting of strings
    preprocessor   = data["PreProcessor"]  # Formatting of preprocessor directives
    stringpreproc  = data["StringPreProc"] # Formatting of strings within preprocessor directives
    blockcomment   = data["BlockComment"]  # Formatting of block comments
    linecomment    = data["LineComment"]   # Formatting of line comments
    linenum        = data["LineNum"]       # Formatting of line numbers
    operator       = data["Operator"]      # Formatting of operators

    if len(data["Keywords"]) < 4:
        logging.error("There should be at least four items to match the number of keyword groups defined in the language definitions")
        return

    for i, attr in enumerate(data["Keywords"]):
        if isinstance(attr, str):
            data["Keywords"][i] = data[attr]

    keywords = [attribute for attribute in data["Keywords"]]

    def convert_rgb(rgb):
        assert(rgb.startswith("#"))

        return "rgb:{0}".format(rgb[1:])

    def get_attr(col, attr):
        return attr in col and col[attr]

    def modify_face(face, data, attr=True):
        face.color_fg = convert_rgb(data["Colour"])
        if attr:
            face.bold = get_attr(data, "Bold")
            face.italic = get_attr(data, "Italic")
            face.underline = get_attr(data, "Underline")

        return face

    theme = []
    with open(path, "w") as fout:
        theme.append("# Kakoune {0} color scheme".format(name_theme))

        if description:
            theme.append("# {0}".format(description))

        face_default = KakouneFace("Default", "default")
        if default:
            face_default = modify_face(face_default, default)

        if canvas:
            face_default.color_bg = convert_rgb(canvas["Colour"])

        theme.append("face Default {0}".format(face_default))

        face_value = KakouneFace("value", "red")
        if number:
            face_value = modify_face(face_value, number)
            theme.append("face value {0}".format(face_value))

        ## XXX: Unused
        ##face_escape = KakouneFace()

        face_string = KakouneFace("string", "magenta")
        if string:
            face_string = modify_face(face_string, string)
            theme.append("face string {0}".format(face_string))

        face_meta = KakouneFace("meta", "magenta")
        if preprocessor:
            face_meta = modify_face(face_meta, preprocessor)
            theme.append("face meta {0}".format(face_meta))

        face_module = KakouneFace("module", "green")
        if stringpreproc:
            face_module = modify_face(face_module, stringpreproc)
            theme.append("face module {0}".format(face_module))

        face_comment = KakouneFace("comment", "cyan")
        if linecomment:
            face_comment = modify_face(face_comment, linecomment)
            theme.append("face comment {0}".format(face_comment))
        elif blockcomment:
            face_comment = modify_face(face_comment, blockcomment)
            theme.append("face comment {0}".format(face_comment))

        face_linenumbers = KakouneFace("LineNumbers", "default")
        if linenum:
            face_linenumbers = modify_face(face_linenumbers, linenum)
            theme.append("face LineNumbers {0}".format(face_linenumbers))

        face_operator = KakouneFace("operator", "yellow")
        if operator:
            face_operator = modify_face(face_operator, operator)
            theme.append("face operator {0}".format(face_operator))

        face_keyword = KakouneFace("keyword", "blue")
        face_keyword = modify_face(face_keyword, keywords[0])
        theme.append("face keyword {0}".format(face_keyword))

        face_builtin = KakouneFace("builtin", "default", bold=True)
        face_builtin = modify_face(face_builtin, keywords[1])
        theme.append("face builtin {0}".format(face_builtin))

        face_function = KakouneFace("function", "cyan")
        face_function = modify_face(face_function, keywords[2])
        theme.append("face function {0}".format(face_function))

        face_attribute = KakouneFace("attribute", "green")
        face_attribute = modify_face(face_attribute, keywords[3])
        theme.append("face attribute {0}".format(face_attribute))

        fout.write("\n".join(theme))


def convert_themes(dir_themes, dir_out):
    logging.info("walking through directory: %s", dir_themes)

    for path_directory, _, filenames in os.walk(dir_themes):
        for filename in filenames:
            path = os.path.join(path_directory, filename)
            name_theme = filename.lower()
            data = None

            if not name_theme.endswith(".theme"):
                logging.info("File doesn't end with the .theme extension, skipping: %s", filename)
                continue

            name_theme = name_theme[:-len(".theme")]

            try:
                logging.info("reading file: %s", path)

                with open(path, "r") as fin:
                    data = fin.read()

                if data:
                    logging.debug("raw LUA: %s", data)

                    ## XXX: re.DOTALL doesn't do anything, pass the regex flag (?s) instead
                    data = re.sub(r"(?s)--\[\[.*?\]\]", "", data)
                    data = re.sub(r"^\h*--.*", "", data)

                    logging.debug("filtered LUA: %s", data)

                    data = lua.decode("{ %s }" % data)
            except IOError as e:
                logging.error("Unable to open file: %s", e)
                continue
            except lua.ParseError as e:
                logging.error("Unable to decode LUA: %s", e)
                continue

            if not data:
                logging.error("No data loaded, skipping")
                continue

            logging.debug("resulting Python data: %s", data)

            data = collections.defaultdict(dict, data)
            write_theme(os.path.join(dir_out, "{0}.kak".format(name_theme)), name_theme, data)

def get_opt(av):
    parser = argparse.ArgumentParser(description="Convert `highlight` themes into `kak` ones")

    parser.add_argument("-d", "--debug", action="store_true", help="Print debug messages")
    parser.add_argument("-t", "--themes-directory", default=Default.DIR_HIGHLIGHT_THEMES, help="Path to the directory containing the themes to convert")
    parser.add_argument("-o", "--output-directory", default=Default.DIR_OUTPUT, help="Path to the directory in which the converted themes will be written")

    return parser.parse_args(av)


def main(av):
    opt = get_opt(av[1:])

    level_logging = logging.DEBUG if opt.debug else logging.INFO
    logging.basicConfig(format="[%(asctime)s][%(levelname)s]: %(message)s", level=level_logging)

    logging.debug("themes directory: %s", opt.themes_directory)

    if not os.path.isdir(opt.output_directory):
        logging.error("No such directory: %s", opt.output_directory)
        return 1

    logging.debug("themes output directory: %s", opt.output_directory)

    convert_themes(opt.themes_directory, opt.output_directory)

    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
