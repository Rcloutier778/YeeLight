# -*- coding: utf-8 -*-
"""
tkcolorpicker - Alternative to colorchooser for Tkinter.
Copyright 2017 Juliette Monsel <j_4321@protonmail.com>

tkcolorpicker is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

tkcolorpicker is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  if not, see <http://www.gnu.org/licenses/>.

HSV gradient bar
"""

import math
from tkcolorpicker.functions import tk, round2, rgb_to_hexa, hue2col


class TemperatureGradBar(tk.Canvas):
    """HSV gradient colorbar with selection cursor."""

    def __init__(self, parent, tempColor=4000, height=11, width=500, variable=None,
                 **kwargs):
        """
        Create a TemperatureGradBar.

        Keyword arguments:
            * parent: parent window
            * tempColor: initially selected tempColor value
            * variable: IntVar linked to the alpha value
            * height, width, and any keyword argument accepted by a tkinter Canvas
        """
        tk.Canvas.__init__(self, parent, width=width, height=height, **kwargs)
        
        self._variable = variable
        if variable is not None:
            try:
                tempColor = int(variable.get())
            except Exception:
                pass
        else:
            self._variable = tk.IntVar(self)
       
        tempColor-=1500
        if tempColor > 5200:
            tempColor = 5200
        elif tempColor < 1500:
            tempColor = 1500
        
        try:
            self._variable.trace_add("write", self._update_temperature)
        except Exception:
            self._variable.trace("w", self._update_temperature)

        self.gradient = tk.PhotoImage(master=self, width=width, height=height)

        self.bind('<Configure>', lambda e: self._draw_gradient(tempColor))
        self.bind('<ButtonPress-1>', self._on_click)
        self.bind('<B1-Motion>', self._on_move)

    def _draw_gradient(self, tempColor):
        """Draw the gradient and put the cursor on tempColor."""
        self.delete("gradient")
        self.delete("cursor")
        del self.gradient
        width = self.winfo_width()
        height = self.winfo_height()

        self.gradient = tk.PhotoImage(master=self, width=width, height=height)

        line = []
        for i in range(width):
            line.append(rgb_to_hexa(*self.calcColor(int(i/width * 9000)+1500)))
        line = "{" + " ".join(line) + "}"
        self.gradient.put(" ".join([line for j in range(height)]))
        self.create_image(0, 0, anchor="nw", tags="gardient",
                          image=self.gradient)
        self.lower("gradient")

        x = tempColor / 5200. * width
        self.create_line(x, 0, x, height, width=2, tags='cursor')

    def _on_click(self, event):
        """Move selection cursor on click."""
        x = event.x
        self.coords('cursor', x, 0, x, self.winfo_height())
        self._variable.set(round2((5200. * x) / self.winfo_width()))

    def _on_move(self, event):
        """Make selection cursor follow the cursor."""
        w = self.winfo_width()
        x = min(max(event.x, 0), w)
        self.coords('cursor', x, 0, x, self.winfo_height())
        self._variable.set(round2((5200. * x) / w))
        print(self._variable.get())
        print(x)

    def _update_temperature(self, *args):
        tmpColor = int(self._variable.get())

        self.set(tmpColor)
        self._variable.set(tmpColor+1500)
        self.event_generate("<<TempChanged>>")

    def get(self):
        """Return tempColor of color under cursor."""
        coords = self.coords('cursor')
        return round2(5200 * coords[0] / self.winfo_width())

    def set(self, tempColor):
        """Set cursor position on the color corresponding to the tempColor value."""
        x = tempColor / 5200. * self.winfo_width()
        self.coords('cursor', x, 0, x, self.winfo_height())
        self._variable.set(tempColor)

    def calcColor(self, tmpKelvin):
        tmpCalc=0.0
        #print('kelvin',tmpKelvin)
        'Temperature must fall between 1500 and 40000 degrees'
        if tmpKelvin < 1500:
            tmpKelvin = 1500
        if tmpKelvin > 40000:
            tmpKelvin = 40000
        
        'All calculations require tmpKelvin \ 100, so only do the conversion once'
        tmpKelvin = tmpKelvin / 100

        'Calculate each color in turn'
        
        'First: red'
        if tmpKelvin <= 66:
            r = 255
        else:
            'Note: the R-squared value for this approximation is .988'
            tmpCalc = tmpKelvin - 60
            tmpCalc = 329.698727446 * (math.pow(tmpCalc,-0.1332047592))
            r = tmpCalc
            if r < 0:
                r = 0
            if r > 255:
                r = 255
        'Second: green'
        if tmpKelvin <= 66:
            'Note: the R-squared value for this approximation is .996'
            tmpCalc = tmpKelvin
            tmpCalc = 99.4708025861 * math.log(tmpCalc) - 161.1195681661
            g = tmpCalc
            if g < 0:
                g = 0
            if g > 255:
                g = 255
        else:
            'Note: the R-squared value for this approximation is .987'
            tmpCalc = tmpKelvin - 60
            tmpCalc = 288.1221695283 * (math.pow(tmpCalc,-0.0755148492))
            g = tmpCalc
            if g < 0:
                g = 0
            if g > 255:
                g = 255
        'Third: blue'
        if tmpKelvin >= 66:
            b = 255
        elif tmpKelvin <= 19:
            b = 0
        else:
            'Note: the R-squared value for this approximation is .998'
            tmpCalc = tmpKelvin - 10
            tmpCalc = 138.5177312231 * math.log(tmpCalc) - 305.0447927307
            
            b = tmpCalc
            if b < 0:
                b = 0
            if b > 255:
                b = 255
        
        return int(r),int(g),int(b)