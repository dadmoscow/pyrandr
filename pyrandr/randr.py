#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2016 Cihangir Akturk <cihangir.akturk@tubitak.gov.tr>
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import print_function
import subprocess as sb
from six import iteritems
from collections import namedtuple


class Mode(object):
    """docstring for Mode"""
    def __init__(self, width, height, freq, current, preferred):
        super(Mode, self).__init__()
        self.width = width
        self.height = height
        self.freq = freq
        self.current = current
        self.preferred = preferred

    def resolution(self, string=False):
        if string:
            return '{0}x{1}'.format(self.width, self.height)
        return self.width, self.height

    def __str__(self):
        return '<{0}, {1}, curr: {2}, pref: {3}>'.format(self.resolution(True),
                                                         self.freq,
                                                         self.current,
                                                         self.preferred)

    __repr__ = __str__


class ScreenSettings(object):
    """docstring for ScreenSettings"""
    def __init__(self):
        super(ScreenSettings, self).__init__()

        self.resolution = (0, 0)
        self.is_primary = False
        self.is_enabled = True
        self.rotation = None
        self.position = None
        self.dirty = None
        self.is_connected = True
        self.change_table = {"resolution": False,
                             "is_primary": False,
                             "is_enabled": False,
                             "rotation": False,
                             "position": False,
                             "dirty": False,
                             "is_connected": False}


class Screen(object):
    def __init__(self, name, primary, rot, modes):
        super(Screen, self).__init__()
        self.__name = name
        self.__set = ScreenSettings()

        # list of Modes (width, height)
        self.supported_modes = modes

        self.curr_mode = [item for item in modes if item.current]
        if self.curr_mode:
            self.curr_mode = self.curr_mode[0]

        self.__set.rotation = rot

        self.__set.is_primary = primary
        self.__set.is_enabled = bool(self.curr_mode)
        self.__set.is_connected = bool(self.supported_modes)
        if self.curr_mode:
            self.__set.resolution = self.curr_mode.resolution()

    @property
    def name(self):
        return self.__name

    @property
    def is_changed(self):
        return self.__set.change_table

    @property
    def is_connected(self):
        return self.__set.is_connected

    @property
    def is_enabled(self):
        return self.__set.is_enabled

    @is_enabled.setter
    def is_enabled(self, enable):
        """Enable or disable the output

        :enable: bool

        """
        if enable != self.__set.is_enabled:
            self.__set.is_enabled = not self.__set.is_enabled
            self.__set.change_table["is_enabled"] = not self.__set.change_table["is_enabled"]

    @property
    def is_primary(self):
        return self.__set.is_primary

    @is_primary.setter
    def is_primary(self, is_primary):
        """Set this monitor as primary

        :is_primary: bool

        """
        if is_primary != self.__set.is_primary:
            self.__set.is_primary = not self.__set.is_primary
            self.__set.change_table["is_primary"] = not self.__set.change_table["is_primary"]

    @property
    def resolution(self):
        return self.__set.resolution

    @resolution.setter
    def resolution(self, newres, custom=False):
        """Sets the resolution of this screen to the supplied
           @newres parameter.

        :newres: must be a tuple in the form (width, height)

        """
        if not self.is_enabled and not self.__set.change_table["is_enabled"]:
            raise ValueError('The Screen is off')
        if newres != self.__set.resolution:
            if not custom:
                self.check_resolution(newres)
            self.__set.resolution = newres
            self.__set.change_table["resolution"] = True

    @property
    def rotation(self):
        return self.__set.rotation

    @rotation.setter
    def rotation(self, direction):
        """Rotate the output in the specified direction

        :direction: RotateDirection.<name> (one of Normal, Left, Right, Inverted)

        """
        if direction != self.__set.rotation:
            self.__set.rotation = direction
            self.__set.change_table["rotation"] = True

    @property
    def position(self):
        return self.__set.position

    @position.setter
    def position(self, args):
        """Position the output relative to the position
        of another output.

        :relation: PostitonType.<name> (one of Above, Below, LeftOf, RightOf, SameAs)
        :relative_to: str output name (LVDS1, HDMI eg.)
        """
        if args != self.__set.position:
            self.__set.position = args
            self.__set.change_table["position"] = True

    def available_resolutions(self, string=False):
        """

        :param string:
        :return:
        """
        if string:
            return [r.resolution(True) for r in self.supported_modes]
        return [r.resolution() for r in self.supported_modes]

    def check_resolution(self, newres):
        """

        :param newres:
        :return:
        """
        if newres not in self.available_resolutions():
            raise ValueError('Requested resolution is not supported', newres)

    def build_cmd(self):
        # if has changed display settings
        if True in self.__set.change_table.values():
            if not self.name:
                raise ValueError('Cannot apply settings without screen name',
                                 self.name)

            cmd = ['xrandr', '--output', self.name]

            turn_off = False

            # if display be disabled
            if self.__set.change_table['is_enabled'] and not self.is_enabled:
                turn_off = True
                cmd.append('--off')

            # add another settings if display not be disabled
            if not turn_off:
                # set resolution
                if self.is_enabled and self.__set.change_table["resolution"]:
                    cmd.extend(['--mode', '{0}x{1}'.format(*self.__set.resolution)])
                else:
                    cmd.append('--auto')

                if self.__set.change_table["is_primary"] and self.is_primary:
                    cmd.append('--primary')

                if self.__set.change_table["rotation"]:
                    rot = RotateDirection.by_direction[self.__set.rotation]
                    if not rot:
                        raise ValueError('Invalid rotation value',
                                         rot, self.__set.rotation)
                    cmd.extend(['--rotate', rot])

                if self.__set.change_table["position"]:
                    rel, rel_to = self.__set.position
                    rel = PostitonType.by_position[rel]
                    cmd.extend([rel, rel_to])

            # if self.__set.change_table['is_enabled'] and not self.is_enabled:
            #     if has_changed:
            #         raise ValueError('--off: this option cannot be combined with other options')
            #     cmd.append('--off')
            return cmd
        else:
            # return False if has no change
            return False

    def apply_settings(self, default=False):
        """
        Apply setting. If default is True -> apply default best quality setting
        :param default: bool
        """
        if default:
            exec_cmd(['xrandr', '--output', self.name, '--auto'])
        else:
            if True in self.__set.change_table.values():
                exec_cmd(self.build_cmd())
        # reset change table
        for key in self.__set.change_table:
            self.__set.change_table[key] = False

    def __str__(self):
        return '<{0}, primary: {1}, modes: {2}, conn: {3}, rot: {4}, '\
                'enabled: {5}>'.format(self.name,
                                      self.is_primary,
                                      len(self.supported_modes),
                                      self.is_connected,
                                      RotateDirection.by_direction[self.rotation],
                                      self.is_enabled)

    __repr__ = __str__


class RotateDirection(object):
    """
    Class with rotations
    """
    Rotation = namedtuple('Rotation', ['direction', 'name'])

    Normal = Rotation(0, 'normal')
    Left = Rotation(90, 'left')
    Inverted = Rotation(180, 'inverted')
    Right = Rotation(270, 'right')

    rotations = (Normal, Left, Inverted, Right)

    by_name = {k.name: k.direction for k in rotations}
    by_direction = {v: k for k, v in by_name.items()}


class PostitonType(object):
    Position = namedtuple('Position', ['name', 'value'])

    LeftOf = Position('--left-of', 1)
    RightOf = Position('--right-of', 2)
    Above = Position('--above', 3)
    Below = Position('--below', 4)
    SameAs = Position('--same-as', 5)

    positions = (LeftOf, RightOf, Above, Below, SameAs)

    by_name = {k.name: k.value for k in positions}
    by_position = {v: k for k, v in by_name.items()}


def exec_cmd(cmd):
    # throws exception CalledProcessError
    s = sb.check_output(cmd, stderr=sb.STDOUT)
    try:
        s = s.decode()
    except AttributeError:
        pass
    return s.split('\n')


def create_screen(name_str, modes):
    rot = None
    sc_name = name_str.split(' ')[0]

    # if connected
    if modes:
        fr = name_str.split(' ')
        if len(fr) > 2:
            name = name_str.split(' ')[3]
            if name in RotateDirection.by_name:
                rot = name
            else:
                rot = RotateDirection.Normal.direction

    return Screen(sc_name, 'primary' in name_str, rot, modes)


def parse_xrandr(lines):
    import re
    rx = re.compile(r'^\s+(\d+)x(\d+)\s+((?:\d+\.)?\d+)([* ]?)([+ ]?)')
    rxconn = re.compile(r'\bconnected\b')
    rxdisconn = re.compile(r'\bdisconnected\b')

    sc_name_line = None
    sc_name = None
    width = None
    height = None
    freq = None
    current = False
    preferred = False

    screens = []
    modes = []

    for i in lines:
        if re.search(rxconn, i) or re.search(rxdisconn, i):
            if sc_name_line:
                newscreen = create_screen(sc_name_line, modes)
                screens.append(newscreen)
                modes = []

            sc_name_line = i

        else:
            r = re.search(rx, i)
            if r:
                width = int(r.group(1))
                height = int(r.group(2))
                freq = float(r.group(3))
                current = r.group(4).replace(' ', '') == '*'
                preferred = r.group(5).replace(' ', '') == '+'

                newmode = Mode(width, height, freq, current, preferred)
                modes.append(newmode)

    if sc_name_line:
        screens.append(create_screen(sc_name_line, modes))

    return screens


def connected_screens():
    """Get connected screens
    """
    return [s for s in parse_xrandr(exec_cmd('xrandr')) if s.is_connected]


def enabled_screens():
    return [s for s in connected_screens() if s.is_enabled]
