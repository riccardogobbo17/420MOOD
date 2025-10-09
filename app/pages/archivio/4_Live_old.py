import streamlit as st
import pandas as pd
from supabase import create_client, Client
from streamlit_autorefresh import st_autorefresh
import matplotlib.pyplot as plt
from matplotlib.patches import Arc, Circle, Rectangle


class Futsal:
    def __init__(self):

        # Initializes a Blind Football pitch object.
        self.fig = None
        self.ax = None

    def _setup_ax(self, ax, figsize):
        if ax is None:
            self.fig, self.ax = plt.subplots(figsize=figsize)
        else:
            self.ax = ax

    def _draw_pitch(self, orientation='horizontal', half_pitch=False, color=False):
        
        """
        Draws the blind football pitch with specified features.

        Parameters:
        - orientation: Pitch orientation ('horizontal' or 'vertical').
        - half_pitch: If True, only draws the right or upper half of the pitch.
        - color: If True, uses blue field
        .
        """
               
        # Colors
        line_color = '#FFFFFF' if color else 'black'
        background_color = '#007ac0' if color else None
        frame_color = '#e6302f' if color else None

        if background_color:
            if orientation == 'horizontal':
                if not half_pitch:
                    self.ax.add_patch(Rectangle((-2, -2), 44, 24, facecolor=frame_color))
                    self.ax.add_patch(Rectangle((0, 0), 40, 20, facecolor=background_color))
                else:
                    self.ax.add_patch(Rectangle((0, -2), 22, 24, facecolor=frame_color))
                    self.ax.add_patch(Rectangle((0, 0), 20, 20, facecolor=background_color))
            else:
                if not half_pitch:
                    self.ax.add_patch(Rectangle((-2, -2), 24, 44, facecolor=frame_color))
                    self.ax.add_patch(Rectangle((0, 0), 20, 40, facecolor=background_color))
                else:
                    self.ax.add_patch(Rectangle((-2, 0), 24, 22, facecolor=frame_color))
                    self.ax.add_patch(Rectangle((0, 0), 20, 20, facecolor=background_color))

        if orientation == 'horizontal':
        
            if not half_pitch:
                
                # Generate a tactical representation of a pitch in horizontal position.
            
                # Pitch Outline
                self.ax.plot([0, 0], [0, 20], color=line_color)
                self.ax.plot([0, 40], [20, 20], color=line_color)
                self.ax.plot([40, 40], [20, 0], color=line_color)
                self.ax.plot([40, 0], [0, 0], color=line_color)

                # Centre Line, Circle, Spot
                self.ax.plot([20, 20], [0, 20], color=line_color)
                centre_circle = Circle((20, 10), 3, color=line_color, fill=False)
                centre_spot = Circle((20, 10), 0.12, color=line_color)
                self.ax.add_patch(centre_circle)
                self.ax.add_patch(centre_spot)

                # Penalty Spot
                left_penalty_spot = Circle((6, 10), 0.12, color=line_color)
                left_double_penalty_spot = Circle((10, 10), 0.12, color=line_color)
                left_double_penalty_spot_1 = Circle((10, 5), 0.06, color=line_color)
                left_double_penalty_spot_2 = Circle((10, 15), 0.06, color=line_color)

                right_penalty_spot = Circle((34, 10), 0.12, color=line_color)
                right_double_penalty_spot = Circle((30, 10), 0.12, color=line_color)
                right_double_penalty_spot_1 = Circle((30, 5), 0.06, color=line_color)
                right_double_penalty_spot_2 = Circle((30, 15), 0.06, color=line_color)

                self.ax.plot([5, 5], [9.7, 10.3], color=line_color, linewidth=0.75)
                self.ax.plot([35, 35], [9.7, 10.3], color=line_color, linewidth=0.75)

                self.ax.add_patch(left_penalty_spot)
                self.ax.add_patch(left_double_penalty_spot)
                self.ax.add_patch(left_double_penalty_spot_1)
                self.ax.add_patch(left_double_penalty_spot_2)
                self.ax.add_patch(right_penalty_spot)
                self.ax.add_patch(right_double_penalty_spot)
                self.ax.add_patch(right_double_penalty_spot_1)
                self.ax.add_patch(right_double_penalty_spot_2)

                # Penalty Area - Left
                area_left_up = Arc((0, 11.83), height=12, width=12, angle=0, theta1=0, theta2=90, color=line_color)
                area_left_down = Arc((0, 8.17), height=12, width=12, angle=270, theta1=0, theta2=90, color=line_color)
                self.ax.plot([6, 6], [8.17, 11.83], color=line_color, linewidth=1)
                self.ax.add_patch(area_left_down)
                self.ax.add_patch(area_left_up)

                # Penalty Area - Right
                area_right_up = Arc((40, 11.83), height=12, width=12, angle=90, theta1=0, theta2=90, color=line_color)
                area_right_down = Arc((40, 8.17), height=12, width=12, angle=180, theta1=0, theta2=90, color=line_color)
                self.ax.plot([34, 34], [8.17, 11.83], color=line_color, linewidth=1)
                self.ax.add_patch(area_right_down)
                self.ax.add_patch(area_right_up)

                # Goal
                self.ax.plot([0, 0], [8.5, 11.5], color=line_color, linewidth=3.5)
                self.ax.plot([40, 40], [8.5, 11.5], color=line_color, linewidth=3.5)

                # Sustitution lines
                self.ax.plot([10, 10], [19.7, 20.3], color=line_color)
                self.ax.plot([15, 15], [19.7, 20.3], color=line_color)
                self.ax.plot([25, 25], [19.7, 20.3], color=line_color)
                self.ax.plot([30, 30], [19.7, 20.3], color=line_color)

                # Corner

                corner_1 = Arc((0, 20), height=1.25, width=1.25, angle=270, theta1=0, theta2=90, color=line_color)
                corner_2 = Arc((40, 20), height=1.25, width=1.25, angle=180, theta1=0, theta2=90, color=line_color)
                corner_3 = Arc((0, 0), height=1.25, width=1.25, angle=0, theta1=0, theta2=90, color=line_color)
                corner_4 = Arc((40, 0), height=1.25, width=1.25, angle=90, theta1=0, theta2=90, color=line_color)

                self.ax.plot([-0.7, -0.4], [5, 5], color=line_color)
                self.ax.plot([-0.7, -0.4], [15, 15], color=line_color)
                self.ax.plot([40.7, 40.4], [5, 5], color=line_color)
                self.ax.plot([40.7, 40.4], [15, 15], color=line_color)
                
                self.ax.add_patch(corner_1)
                self.ax.add_patch(corner_2)
                self.ax.add_patch(corner_3)
                self.ax.add_patch(corner_4)

            else:

                # Generate a tactical representation of the right half of a blind football pitch in a horizontal position.

                # Pitch Outline
                self.ax.plot([0, 0], [0, 20], color=line_color)
                self.ax.plot([0, 20], [20, 20], color=line_color)
                self.ax.plot([20, 20], [20, 0], color=line_color)
                self.ax.plot([20, 0], [0, 0], color=line_color)

                # Centre Circle, Spot
                centre_circle = Arc((0, 10), height=6, width=6, angle=270, theta1=0, theta2=180, color=line_color)
                centre_spot = Circle((0, 10), 0.12, color=line_color)
                self.ax.add_patch(centre_circle)
                self.ax.add_patch(centre_spot)

                # Penalty Spot
                penalty_spot = Circle((14, 10), 0.12, color=line_color)
                double_penalty_spot = Circle((10, 10), 0.12, color=line_color)
                double_penalty_spot_1 = Circle((10, 5), 0.06, color=line_color)
                double_penalty_spot_2 = Circle((10, 15), 0.06, color=line_color)

                self.ax.plot([15, 15], [9.7, 10.3], color=line_color, linewidth=0.75)

                self.ax.add_patch(penalty_spot)
                self.ax.add_patch(double_penalty_spot)
                self.ax.add_patch(double_penalty_spot_1)
                self.ax.add_patch(double_penalty_spot_2)

                # Penalty Area
                area_up = Arc((20, 11.83), height=12, width=12, angle=90, theta1=0, theta2=90, color=line_color)
                area_down = Arc((20, 8.17), height=12, width=12, angle=180, theta1=0, theta2=90, color=line_color)
                self.ax.plot([14, 14], [8.17, 11.83], color=line_color, linewidth=1)
                self.ax.add_patch(area_down)
                self.ax.add_patch(area_up)

                # Goal
                self.ax.plot([20, 20], [8.5, 11.5], color=line_color, linewidth=3.5)

                # Sustitution lines
                self.ax.plot([5, 5], [19.7, 20.3], color=line_color)
                self.ax.plot([10, 10], [19.7, 20.3], color=line_color)

                # Corner

                corner_2 = Arc((20, 20), height=1.25, width=1.25, angle=180, theta1=0, theta2=90, color=line_color)
                corner_4 = Arc((20, 0), height=1.25, width=1.25, angle=90, theta1=0, theta2=90, color=line_color)

                self.ax.plot([20.7, 20.4], [5, 5], color=line_color)
                self.ax.plot([20.7, 20.4], [15, 15], color=line_color)
                
                self.ax.add_patch(corner_2)
                self.ax.add_patch(corner_4)


        elif orientation == "vertical":
                
                if not half_pitch:
                    
                    # Generate a tactical representation of a blind football pitch in a vertical position.

                    # Pitch Outline
                    self.ax.plot([0, 20], [0, 0], color=line_color)
                    self.ax.plot([20, 20], [0, 40], color=line_color)
                    self.ax.plot([20, 0], [40, 40], color=line_color)
                    self.ax.plot([0, 0], [40, 0], color=line_color)

                    # Centre Line, Circle, Spot
                    self.ax.plot([0, 20], [20, 20], color=line_color)
                    centre_circle = Circle((10, 20), 3, color=line_color, fill=False)
                    centre_spot = Circle((10, 20), 0.12, color=line_color)
                    self.ax.add_patch(centre_circle)
                    self.ax.add_patch(centre_spot)

                    # Penalty Spot
                    left_penalty_spot = Circle((10, 6), 0.12, color=line_color)
                    left_double_penalty_spot = Circle((10, 10), 0.12, color=line_color)
                    left_double_penalty_spot_1 = Circle((5, 10), 0.06, color=line_color)
                    left_double_penalty_spot_2 = Circle((15, 10), 0.06, color=line_color)
                    right_penalty_spot = Circle((10, 34), 0.12, color=line_color)

                    right_double_penalty_spot = Circle((10, 30), 0.12, color=line_color)
                    right_double_penalty_spot_1 = Circle((5, 30), 0.06, color=line_color)
                    right_double_penalty_spot_2 = Circle((15, 30), 0.06, color=line_color)

                    self.ax.plot([9.7, 10.3], [5, 5], color=line_color, linewidth=0.75)
                    self.ax.plot([9.7, 10.3], [35, 35], color=line_color, linewidth=0.75)

                    self.ax.add_patch(left_penalty_spot)
                    self.ax.add_patch(left_double_penalty_spot)
                    self.ax.add_patch(left_double_penalty_spot_1)
                    self.ax.add_patch(left_double_penalty_spot_2)
                    self.ax.add_patch(right_penalty_spot)
                    self.ax.add_patch(right_double_penalty_spot)
                    self.ax.add_patch(right_double_penalty_spot_1)
                    self.ax.add_patch(right_double_penalty_spot_2)

                    # Penalty Area - Up
                    area_left_up = Arc((8.17, 40), height=12, width=12, angle=180, theta1=0, theta2=90, color=line_color)
                    area_right_up = Arc((11.83, 40), height=12, width=12, angle=270, theta1=0, theta2=90, color=line_color)
                    self.ax.plot([8.17, 11.83], [34, 34], color=line_color, linewidth=1)
                    self.ax.add_patch(area_left_up)
                    self.ax.add_patch(area_right_up)
                    
                    # Penalty Area - Down
                    area_left_down = Arc((8.17, 0), height=12, width=12, angle=90, theta1=0, theta2=90, color=line_color)
                    area_right_down = Arc((11.83, 0), height=12, width=12, angle=0, theta1=0, theta2=90, color=line_color)
                    self.ax.plot([8.17, 11.83], [6, 6], color=line_color, linewidth=1)
                    self.ax.add_patch(area_left_down)
                    self.ax.add_patch(area_right_down)

                    # Goal
                    self.ax.plot([8.5, 11.5], [0, 0], color=line_color, linewidth=3.5)
                    self.ax.plot([8.5, 11.5], [40, 40], color=line_color, linewidth=3.5)
                
                    # Substitution lines
                    self.ax.plot([-0.3, 0.3], [10, 10], color=line_color)
                    self.ax.plot([-0.3, 0.3], [15, 15], color=line_color)
                    self.ax.plot([-0.3, 0.3], [25, 25], color=line_color)
                    self.ax.plot([-0.3, 0.3], [30, 30], color=line_color)

                    # Corner
                    corner_1 = Arc((20, 0), height=1.25, width=1.25, angle=90, theta1=0, theta2=90, color=line_color)
                    corner_2 = Arc((20, 40), height=1.25, width=1.25, angle=180, theta1=0, theta2=90, color=line_color)
                    corner_3 = Arc((0, 0), height=1.25, width=1.25, angle=0, theta1=0, theta2=90, color=line_color)
                    corner_4 = Arc((0, 40), height=1.25, width=1.25, angle=270, theta1=0, theta2=90, color=line_color)

                    self.ax.plot([5, 5], [-0.7, -0.4], color=line_color)
                    self.ax.plot([15, 15], [-0.7, -0.4], color=line_color)
                    self.ax.plot([5, 5], [40.7, 40.4], color=line_color)
                    self.ax.plot([15, 15], [40.7, 40.4], color=line_color)

                    self.ax.add_patch(corner_1)
                    self.ax.add_patch(corner_2)
                    self.ax.add_patch(corner_3)
                    self.ax.add_patch(corner_4)

                else:

                    # Generate a tactical representation of the upper half of a blind football pitch in a vertical position.

                    # Pitch Outline
                    self.ax.plot([0, 0], [0, 20], color=line_color)
                    self.ax.plot([0, 20], [20, 20], color=line_color)
                    self.ax.plot([20, 20], [20, 0], color=line_color)
                    self.ax.plot([20, 0], [0, 0], color=line_color)
                    
                    # Centre Circle, Spot
                    centre_circle = Arc((10, 0), height=6, width=6, angle=0, theta1=0, theta2=180, color=line_color)
                    centre_spot = Circle((10, 0), 0.12, color=line_color)
                    self.ax.add_patch(centre_circle)
                    self.ax.add_patch(centre_spot)

                    # Penalty Spot
                    penalty_spot = Circle((10, 14), 0.12, color=line_color)
                    double_penalty_spot = Circle((10, 10), 0.12, color=line_color)
                    double_penalty_spot_1 = Circle((5, 10), 0.06, color=line_color)
                    double_penalty_spot_2 = Circle((15, 10), 0.06, color=line_color)

                    self.ax.plot([9.7, 10.3], [15, 15], color=line_color, linewidth=0.75)

                    self.ax.add_patch(penalty_spot)
                    self.ax.add_patch(double_penalty_spot)
                    self.ax.add_patch(double_penalty_spot_1)
                    self.ax.add_patch(double_penalty_spot_2)

                    # Penalty Area
                    area_left = Arc((8.17, 20), height=12, width=12, angle=180, theta1=0, theta2=90, color=line_color)
                    area_right = Arc((11.83, 20), height=12, width=12, angle=270, theta1=0, theta2=90, color=line_color)
                    self.ax.plot([8.17, 11.83], [14, 14], color=line_color, linewidth=1)
                    self.ax.add_patch(area_left)
                    self.ax.add_patch(area_right)

                    # Goal
                    self.ax.plot([8.5, 11.5], [20, 20], color=line_color, linewidth=3.5)

                    # Substitution lines
                    self.ax.plot([-0.3, 0.3], [5, 5], color=line_color)
                    self.ax.plot([-0.3, 0.3], [10, 10], color=line_color)

                    # Corner
                    corner_2 = Arc((20, 20), height=1.25, width=1.25, angle=180, theta1=0, theta2=90, color=line_color)
                    corner_4 = Arc((0, 20), height=1.25, width=1.25, angle=270, theta1=0, theta2=90, color=line_color)

                    self.ax.plot([5, 5], [20.7, 20.4], color=line_color)
                    self.ax.plot([15, 15], [20.7, 20.4], color=line_color)

                    self.ax.add_patch(corner_2)
                    self.ax.add_patch(corner_4)

        # Tidy Axes and set equal aspect ratio
        self.ax.axis('off')
        self.ax.axis('equal')

    def draw(self, orientation='horizontal', half_pitch=False, color=False, ax=None, figsize=None):
        
        """
        Public method to draw the blind football pitch.

        Parameters:
        - orientation: Pitch orientation ('horizontal' or 'vertical').
        - half_pitch: If True, only draws the right or upper half of the pitch.
        - ax: Optional custom axes. If None, a new subplot is created.
        - figsize: Optional figure size. If None, default size is used.

        Returns:
        - fig, ax: Figure and axes objects.
        """     
        
        self._setup_ax(ax, figsize)
        self._draw_pitch(orientation, half_pitch, color)
        return self.fig, self.ax


class BlindFootball:
    def __init__(self):

        # Initializes a Blind Football pitch object.
        self.fig = None
        self.ax = None

    def _setup_ax(self, ax, figsize):
        if ax is None:
            self.fig, self.ax = plt.subplots(figsize=figsize)
        else:
            self.ax = ax

    def _draw_pitch(self, orientation='horizontal', half_pitch=False):
        
        """
        Draws the blind football pitch with specified features.

        Parameters:
        - orientation: Pitch orientation ('horizontal' or 'vertical').
        - half_pitch: If True, only draws the right or upper half of the pitch.
        """
               
        if orientation == 'horizontal':
        
            if not half_pitch:
                
                # Generate a tactical representation of a blind football pitch in horizontal position.
            
                # Pitch Outline
                self.ax.plot([0, 0], [0, 20], color="black")
                self.ax.plot([0, 40], [20, 20], color="black")
                self.ax.plot([40, 40], [20, 0], color="black")
                self.ax.plot([40, 0], [0, 0], color="black")

                # Third Line
                self.ax.plot([12, 12], [0, 20], color="black", linestyle="--", dashes=(5, 15))
                self.ax.plot([28, 28], [0, 20], color="black", linestyle="--", dashes=(5, 15))

                # Centre Line, Circle, Spot
                self.ax.plot([20, 20], [0, 20], color="black")
                centre_circle = Circle((20, 10), 5, color="black", fill=False)
                centre_spot = Circle((20, 10), 0.12, color="black")
                self.ax.add_patch(centre_circle)
                self.ax.add_patch(centre_spot)

                # Penalty Spot
                left_penalty_spot = Circle((6, 10), 0.12, color="black")
                left_double_penalty_spot = Circle((8, 10), 0.12, color="black")
                right_penalty_spot = Circle((34, 10), 0.12, color="black")
                right_double_penalty_spot = Circle((32, 10), 0.12, color="black")
                self.ax.add_patch(left_penalty_spot)
                self.ax.add_patch(left_double_penalty_spot)
                self.ax.add_patch(right_penalty_spot)
                self.ax.add_patch(right_double_penalty_spot)

                # Goalkeeper Area - Left
                self.ax.plot([0, 2], [12.91, 12.91], color="black")
                self.ax.plot([2, 2], [12.91, 7.09], color="black")
                self.ax.plot([2, 0], [7.09, 7.09], color="black")

                # Goalkeeper Area - Right
                self.ax.plot([40, 38], [12.91, 12.91], color="black")
                self.ax.plot([38, 38], [12.91, 7.09], color="black")
                self.ax.plot([38, 40], [7.09, 7.09], color="black")

                # Penalty Area - Left
                area_left_up = Arc((0, 11.83), height=12, width=12, angle=0, theta1=0, theta2=90, color="black")
                area_left_down = Arc((0, 8.17), height=12, width=12, angle=270, theta1=0, theta2=90, color="black")
                self.ax.plot([6, 6], [8.17, 11.83], color="black", linewidth=1)
                self.ax.add_patch(area_left_down)
                self.ax.add_patch(area_left_up)

                # Penalty Area - Right
                area_right_up = Arc((40, 11.83), height=12, width=12, angle=90, theta1=0, theta2=90, color="black")
                area_right_down = Arc((40, 8.17), height=12, width=12, angle=180, theta1=0, theta2=90, color="black")
                self.ax.plot([34, 34], [8.17, 11.83], color="black", linewidth=1)
                self.ax.add_patch(area_right_down)
                self.ax.add_patch(area_right_up)

                # Goal
                self.ax.plot([0, 0], [8.17, 11.83], color="black", linewidth=3.5)
                self.ax.plot([40, 40], [8.17, 11.83], color="black", linewidth=3.5)

            else:

                # Generate a tactical representation of the right half of a blind football pitch in a horizontal position.

                # Pitch Outline
                self.ax.plot([0, 0], [0, 20], color="black")
                self.ax.plot([0, 20], [20, 20], color="black")
                self.ax.plot([20, 20], [20, 0], color="black")
                self.ax.plot([20, 0], [0, 0], color="black")

                # Third Line
                self.ax.plot([8, 8], [0, 20], color="black", linestyle="--", dashes=(5, 15))

                # Centre Circle, Spot
                centre_circle = Arc((0, 10), height=10, width=10, angle=270, theta1=0, theta2=180, color="black")
                centre_spot = Circle((0, 10), 0.12, color="black")
                self.ax.add_patch(centre_circle)
                self.ax.add_patch(centre_spot)

                # Penalty Spot
                penalty_spot = Circle((14, 10), 0.12, color="black")
                double_penalty_spot = Circle((12, 10), 0.12, color="black")
                self.ax.add_patch(penalty_spot)
                self.ax.add_patch(double_penalty_spot)

                # Goalkeeper Area
                self.ax.plot([20, 18], [12.91, 12.91], color="black")
                self.ax.plot([18, 18], [12.91, 7.09], color="black")
                self.ax.plot([18, 20], [7.09, 7.09], color="black")

                # Penalty Area
                area_up = Arc((20, 11.83), height=12, width=12, angle=90, theta1=0, theta2=90, color="black")
                area_down = Arc((20, 8.17), height=12, width=12, angle=180, theta1=0, theta2=90, color="black")
                self.ax.plot([14, 14], [8.17, 11.83], color="black", linewidth=1)
                self.ax.add_patch(area_down)
                self.ax.add_patch(area_up)

                # Goal
                self.ax.plot([20, 20], [8.17, 11.83], color="black", linewidth=3.5)

        elif orientation == "vertical":
                
                if not half_pitch:
                    
                    # Generate a tactical representation of a blind football pitch in a vertical position.

                    # Pitch Outline
                    self.ax.plot([0, 20], [0, 0], color="black")
                    self.ax.plot([20, 20], [0, 40], color="black")
                    self.ax.plot([20, 0], [40, 40], color="black")
                    self.ax.plot([0, 0], [40, 0], color="black")

                    # Third Line
                    self.ax.plot([0, 20], [12, 12], color="black", linestyle="--", dashes=(5, 15))
                    self.ax.plot([0, 20], [28, 28], color="black", linestyle="--", dashes=(5, 15))

                    # Centre Line, Circle, Spot
                    self.ax.plot([0, 20], [20, 20], color="black")
                    centre_circle = Circle((10, 20), 5, color="black", fill=False)
                    centre_spot = Circle((10, 20), 0.12, color="black")
                    self.ax.add_patch(centre_circle)
                    self.ax.add_patch(centre_spot)

                    # Penalty Spot
                    left_penalty_spot = Circle((10, 6), 0.12, color="black")
                    left_double_penalty_spot = Circle((10, 8), 0.12, color="black")
                    right_penalty_spot = Circle((10, 34), 0.12, color="black")
                    right_double_penalty_spot = Circle((10, 32), 0.12, color="black")
                    self.ax.add_patch(left_penalty_spot)
                    self.ax.add_patch(left_double_penalty_spot)
                    self.ax.add_patch(right_penalty_spot)
                    self.ax.add_patch(right_double_penalty_spot)

                    # Goalkeeper Area - Up 
                    self.ax.plot([12.91, 12.91], [40, 38], color="black")
                    self.ax.plot([12.91, 7.09], [38, 38], color="black")
                    self.ax.plot([7.09, 7.09], [38, 40], color="black")
                    
                    # Goalkeeper Area - Down
                    self.ax.plot([12.91, 12.91], [0, 2], color="black")
                    self.ax.plot([12.91, 7.09], [2, 2], color="black")
                    self.ax.plot([7.09, 7.09], [2, 0], color="black")

                    # Penalty Area - Up
                    area_left_up = Arc((8.17, 40), height=12, width=12, angle=180, theta1=0, theta2=90, color="black")
                    area_right_up = Arc((11.83, 40), height=12, width=12, angle=270, theta1=0, theta2=90, color="black")
                    self.ax.plot([8.17, 11.83], [34, 34], color="black", linewidth=1)
                    self.ax.add_patch(area_left_up)
                    self.ax.add_patch(area_right_up)
                    
                    # Penalty Area - Down
                    area_left_down = Arc((8.17, 0), height=12, width=12, angle=90, theta1=0, theta2=90, color="black")
                    area_right_down = Arc((11.83, 0), height=12, width=12, angle=0, theta1=0, theta2=90, color="black")
                    self.ax.plot([8.17, 11.83], [6, 6], color="black", linewidth=1)
                    self.ax.add_patch(area_left_down)
                    self.ax.add_patch(area_right_down)

                    # Goal
                    self.ax.plot([8.17, 11.83], [0, 0], color="black", linewidth=3.5)
                    self.ax.plot([8.17, 11.83], [40, 40], color="black", linewidth=3.5)
                
                else:

                    # Generate a tactical representation of the upper half of a blind football pitch in a vertical position.

                    # Pitch Outline
                    self.ax.plot([0, 0], [0, 20], color="black")
                    self.ax.plot([0, 20], [20, 20], color="black")
                    self.ax.plot([20, 20], [20, 0], color="black")
                    self.ax.plot([20, 0], [0, 0], color="black")

                    # Third Line
                    self.ax.plot([0, 20], [8, 8], color="black", linestyle="--", dashes=(5, 15))
                    
                    # Centre Circle, Spot
                    centre_circle = Arc((10, 0), height=10, width=10, angle=0, theta1=0, theta2=180, color="black")
                    centre_spot = Circle((10, 0), 0.12, color="black")
                    self.ax.add_patch(centre_circle)
                    self.ax.add_patch(centre_spot)

                    # Penalty Spot
                    penalty_spot = Circle((10, 14), 0.12, color="black")
                    double_penalty_spot = Circle((10, 12), 0.12, color="black")
                    self.ax.add_patch(penalty_spot)
                    self.ax.add_patch(double_penalty_spot)

                    # Goalkeeper Area
                    self.ax.plot([12.91, 12.91], [20, 18], color="black")
                    self.ax.plot([12.91, 7.09], [18, 18], color="black")
                    self.ax.plot([7.09, 7.09], [18, 20], color="black")

                    # Penalty Area
                    area_left = Arc((8.17, 20), height=12, width=12, angle=180, theta1=0, theta2=90, color="black")
                    area_right = Arc((11.83, 20), height=12, width=12, angle=270, theta1=0, theta2=90, color="black")
                    self.ax.plot([8.17, 11.83], [14, 14], color="black", linewidth=1)
                    self.ax.add_patch(area_left)
                    self.ax.add_patch(area_right)

                    # Goal
                    self.ax.plot([8.17, 11.83], [20, 20], color="black", linewidth=3.5)

        # Tidy Axes and set equal aspect ratio
        self.ax.axis('off')
        self.ax.axis('equal')

    def draw(self, orientation='horizontal', half_pitch=False, ax=None, figsize=None):
        
        """
        Public method to draw the pitch.

        Parameters:
        - orientation: Pitch orientation ('horizontal' or 'vertical').
        - half_pitch: If True, only draws the right or upper half of the pitch.
        - ax: Optional custom axes. If None, a new subplot is created.
        - figsize: Optional figure size. If None, default size is used.

        Returns:
        - fig, ax: Figure and axes objects.
        """     
        
        self._setup_ax(ax, figsize)
        self._draw_pitch(orientation, half_pitch)
        return self.fig, self.ax

def to_seconds(time_str):
    """Converte una stringa 'h:mm:ss.xxx' in secondi float."""
    if pd.isna(time_str):
        return np.nan
    t = time_str.split(':')
    if len(t) == 3:
        h, m, s = t
        return int(h)*3600 + int(m)*60 + float(s)
    else:
        return np.nan

def format_mmss(s):
    if pd.isna(s):
        return ''
    m = int(s // 60)
    s2 = int(round(s % 60))
    return f"{m:02}:{s2:02}"

def calcola_tempo_effettivo(df):
    df_eff = df.copy()
    df_eff['Posizione_sec'] = df_eff['posizione'].apply(to_seconds)

    # Trova indici chiave
    idx_start = 0
    idx_fine_primo = df_eff[df_eff['evento'] == 'Fine primo tempo'].index[0]
    idx_start_secondo = idx_fine_primo + 1
    idx_fine_partita = df_eff[df_eff['evento'] == 'Fine partita'].index[0]

    # Tempi reali (in secondi)
    t_start = df_eff.loc[idx_start, 'Posizione_sec']
    t_fine_primo = df_eff.loc[idx_fine_primo, 'Posizione_sec']
    t_start_secondo = df_eff.loc[idx_start_secondo, 'Posizione_sec']
    t_fine_partita = df_eff.loc[idx_fine_partita, 'Posizione_sec']

    tempo_effettivo_sec = []

    for i, row in df_eff.iterrows():
        t = row['Posizione_sec']
        if i <= idx_fine_primo:
            # Primo tempo
            perc = (t - t_start) / (t_fine_primo - t_start) if (t_fine_primo - t_start) != 0 else 0
            eff = perc * 20 * 60
        elif i >= idx_start_secondo:
            # Secondo tempo
            perc = (t - t_start_secondo) / (t_fine_partita - t_start_secondo) if (t_fine_partita - t_start_secondo) != 0 else 0
            eff = 20 * 60 + perc * 20 * 60
        else:
            eff = np.nan  # Tra fine primo tempo e inizio secondo
        tempo_effettivo_sec.append(eff)

    df_eff['tempoEffettivo_sec'] = tempo_effettivo_sec
    df_eff['tempoEffettivo'] = df_eff['tempoEffettivo_sec'].apply(format_mmss)

    return df_eff['tempoEffettivo']


def differenza_tempi(t1: str, t2: str, format: str = '') -> str:
    """
    Calcola la differenza tra due stringhe temporali e restituisce il risultato nel formato 'MM:SS'.

    Args:
        t1 (str): Tempo iniziale.
        t2 (str): Tempo finale.
        format (str): Specifica il formato degli input. 
                      Lasciare vuoto per 'H:MM:SS.sss', oppure passare 'MM:SS'.

    Returns:
        str: Differenza nel formato 'MM:SS'.
    """
    if format == 'MM:SS':
        t1 = '00:' + t1
        t2 = '00:' + t2
    
    td1 = pd.to_timedelta(t1)
    td2 = pd.to_timedelta(t2)
    diff = td2 - td1
    total_seconds = int(diff.total_seconds())
    minutes = total_seconds // 60
    seconds = total_seconds % 60
    return f"{minutes:02}:{seconds:02}"




def calcola_tempo_reale(df):# Calcola il tempo reale di gioco per ciascun evento
    tempi_reali_gioco = []

    for i, row in df.iterrows():
        if i <= idx_fine_primo:
            tempo = differenza_tempi(t_start, row['posizione'])
        elif i >= idx_start_secondo:
            tempo = differenza_tempi(t_start_secondo, row['posizione'])
        else:
            tempo = ''
        tempi_reali_gioco.append(tempo)
    return tempi_reali_gioco


def tag_primo_secondo_tempo(df):
    # Crea una nuova colonna "tempo" per indicare se l'evento appartiene al primo o secondo tempo
    tempo_periodo = []

    for i in df.index:
        if i <= idx_fine_primo:
            tempo_periodo.append("Primo tempo")
        elif i >= idx_start_secondo:
            tempo_periodo.append("Secondo tempo")
        else:
            tempo_periodo.append("Intervallo")

    return tempo_periodo


def get_giocatori_in_campo(row):
    giocatori = [row['portiere']]
    for col in ['quartetto', 'quartetto_1', 'quartetto_2', 'quartetto_3', 'quartetto_4']:
        if pd.notna(row.get(col)):
            giocatori.append(row[col])
    giocatori = [g for g in giocatori if pd.notna(g) and str(g).strip() != '']
    if len(giocatori) == 5:
        return tuple(sorted(giocatori[1:]))
    else:
        return tuple(sorted(giocatori))


# Funzione unica per calcolare minuti e percentuali con Metodo 3 per singoli, coppie e quartetti
def calcola_minutaggi(df):
    import numpy as np
    from collections import defaultdict
    from itertools import combinations

    def calcola_minuti_percentuali_shifted(df_local, durata_rif, quartetti=False, singoli=False, coppie=False):
        delta_sec = []
        valori_successivi = []

        for i in range(len(df_local) - 1):
            t1 = df_local.loc[i, 'tempoReale']
            t2 = df_local.loc[i + 1, 'tempoReale']
            q_next = df_local.loc[i + 1, 'quartetto_tot']

            if pd.isna(t1) or pd.isna(t2) or t1 == '' or t2 == '' or not isinstance(q_next, tuple) or len(q_next) != 4:
                continue

            td = pd.to_timedelta("00:" + t2) - pd.to_timedelta("00:" + t1)
            delta = max(0, td.total_seconds())

            if quartetti:
                valori_successivi.append((tuple(sorted(q_next)), delta))
            elif singoli:
                for g in q_next:
                    valori_successivi.append((g, delta))
            elif coppie:
                for c in combinations(sorted(q_next), 2):
                    valori_successivi.append((c, delta))

        acc = defaultdict(float)
        for k, d in valori_successivi:
            acc[k] += d

        if quartetti:
            return pd.DataFrame([
                {"Quartetto": k, "Minuti_giocati": t / 60, "Percentuale": 100 * t / durata_rif}
                for k, t in acc.items()
            ]).sort_values(by="Minuti_giocati", ascending=False)
        elif singoli:
            return pd.DataFrame([
                {"Giocatore": k, "Minuti_giocati": t / 60, "Percentuale": 100 * t / durata_rif}
                for k, t in acc.items()
            ]).sort_values(by="Minuti_giocati", ascending=False)
        elif coppie:
            return pd.DataFrame([
                {"Coppia": k, "Minuti_giocati": t / 60, "Percentuale": 100 * t / durata_rif}
                for k, t in acc.items()
            ]).sort_values(by="Minuti_giocati", ascending=False)
        else:
            return pd.DataFrame()

    # Trova indici dei tempi
    idx_fine_primo = df[df['evento'] == 'Fine primo tempo'].index[0]
    idx_start_secondo = idx_fine_primo + 1
    idx_fine_partita = df[df['evento'] == 'Fine partita'].index[0]

    df_1t = df.iloc[:idx_fine_primo + 1].reset_index(drop=True)
    df_2t = df.iloc[idx_start_secondo:idx_fine_partita + 1].reset_index(drop=True)

    # Calcola durate
    def durata_reale_sec(df_local):
        # Funzione helper per pulire i valori di tempo
        def clean_time_value(time_val):
            if pd.isna(time_val) or time_val == '' or time_val is None:
                return "00:00"
            # Rimuovi spazi e caratteri non validi
            time_str = str(time_val).strip()
            # Se è una stringa vuota dopo lo strip, usa 00:00
            if not time_str:
                return "00:00"
            # Se non contiene ':', aggiungi 00: all'inizio
            if ':' not in time_str:
                return "00:00"
            return time_str
        
        # Pulisci i valori di tempo
        tempo_reale_clean = df_local['tempoReale'].apply(clean_time_value)
        tempo_reale_next_clean = tempo_reale_clean.shift(-1).fillna("00:00")
        
        # Assicurati che tutti i valori abbiano il formato corretto per timedelta
        tempo_reale_clean = tempo_reale_clean.fillna("00:00")
        tempo_reale_next_clean = tempo_reale_next_clean.fillna("00:00")
        
        # Converti in timedelta
        delta = (
            pd.to_timedelta("00:" + tempo_reale_next_clean).dt.total_seconds()
            - pd.to_timedelta("00:" + tempo_reale_clean).dt.total_seconds()
        ).values
        return np.clip(delta, a_min=0, a_max=None).sum()

    durata_totale_sec = durata_reale_sec(df)
    durata_primo_sec = durata_reale_sec(df_1t)
    durata_secondo_sec = durata_reale_sec(df_2t)

    return {
        "singoli_tot": calcola_minuti_percentuali_shifted(df, durata_totale_sec, singoli=True),
        "singoli_1t": calcola_minuti_percentuali_shifted(df_1t, durata_primo_sec, singoli=True),
        "singoli_2t": calcola_minuti_percentuali_shifted(df_2t, durata_secondo_sec, singoli=True),
        "coppie_tot": calcola_minuti_percentuali_shifted(df, durata_totale_sec, coppie=True),
        "coppie_1t": calcola_minuti_percentuali_shifted(df_1t, durata_primo_sec, coppie=True),
        "coppie_2t": calcola_minuti_percentuali_shifted(df_2t, durata_secondo_sec, coppie=True),
        "quartetti_tot": calcola_minuti_percentuali_shifted(df, durata_totale_sec, quartetti=True),
        "quartetti_1t": calcola_minuti_percentuali_shifted(df_1t, durata_primo_sec, quartetti=True),
        "quartetti_2t": calcola_minuti_percentuali_shifted(df_2t, durata_secondo_sec, quartetti=True),
    }


def filtra_per_tempo(df, tempo='primo'):
    idx_fine_primo = df[df['evento'] == 'Fine primo tempo'].index[0]
    idx_fine_partita = df[df['evento'] == 'Fine partita'].index[0]
    if tempo == 'primo':
        return df.loc[:idx_fine_primo]
    elif tempo == 'secondo':
        return df.loc[idx_fine_primo+1:idx_fine_partita]
    else:
        return df


def plot_tiri_per_zona(df, squadra='Noi'):

    df_tiri = df[(df['squadra'] == squadra) & (df['evento'] == 'Tiro')].copy()
    df_tiri['zona'] = pd.to_numeric(df_tiri['dove'], errors='coerce').fillna(-1).astype(int)

    # Conta gli esiti per zona
    zone_stats = {}
    for zona, gruppo in df_tiri.groupby('zona'):
        esiti = gruppo['esito'].value_counts().to_dict()
        zone_stats[zona] = {
            "Gol": esiti.get("Gol", 0),
            "Parata": esiti.get("Parata", 0),
            "Ribattuto": esiti.get("Ribattuto", 0),
            "Fuori": esiti.get("Fuori", 0),
            "Tot": len(gruppo)
        }
    futsal = Futsal()
    # Disegno campo
    fig, ax = futsal.draw(orientation='vertical', half_pitch=False, color=False, figsize=(6, 11))

    x_div = [0, 6.66, 13.33, 20]
    y_div = [0, 20, 27, 34, 40]

    for x in x_div:
        ax.plot([x, x], [20 if x != 0 and x != 20 else 0, 40], color='grey', linestyle='--', linewidth=1, zorder=10)

    for y in y_div[1:]:
        ax.plot([0, 20], [y, y], color='grey', linestyle='--', linewidth=1, zorder=10)

    # Zone da 1 a 9
    zone_number = 1
    for i in range(3):
        for j in range(3):
            x_center = x_div[j] + (x_div[j+1] - x_div[j]) / 2
            y_center = y_div[i+1] + (y_div[i+2] - y_div[i+1]) / 2
            stats = zone_stats.get(zone_number, {"Gol": 0, "Parata": 0, "Ribattuto": 0, "Fuori": 0, "Tot": 0})
            label = f"{stats['Gol']}G / {stats['Parata']}P / {stats['Ribattuto']}R / {stats['Fuori']}F / {stats['Tot']}T"
            ax.text(x_center, y_center, label, fontsize=9, weight='bold',
                    color='black', ha='center', va='center', zorder=15)
            zone_number += 1

    # Zona 0
    stats_0 = zone_stats.get(0, {"Gol": 0, "Parata": 0, "Ribattuto": 0, "Fuori": 0, "Tot": 0})
    label_0 = f"{stats_0['Gol']}G / {stats_0['Parata']}P / {stats_0['Ribattuto']}R / {stats_0['Fuori']}F / {stats_0['Tot']}T"
    ax.text(10, 11, label_0, fontsize=9, weight='bold',
            color='black', ha='center', va='center', zorder=15)

    plt.title(f"Tiri effettuati da '{squadra}': G / P / R / F / T", fontsize=13)
    plt.tight_layout()
    return fig

# =============== CONFIGURAZIONE ===============
SUPABASE_URL = "https://jinmmonxjovoccejgwhk.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imppbm1tb254am92b2NjZWpnd2hrIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDk1NTk3NzksImV4cCI6MjA2NTEzNTc3OX0.kapMvgvW-6fng-RhxZV_YFcLnxcXo9Bg2wpDWu_H-5g"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

st.set_page_config(page_title="Live Match Monitor", layout="wide")
st.title("🟢 Monitoraggio Live - Futsal")

# =============== AUTOREFRESH ===============
st_autorefresh(interval=5000, key="live_refresh")

# =============== CARICAMENTO DATI LIVE ===============
eventi = supabase.table("live").select("*").execute().data
df = pd.DataFrame(eventi).reset_index(drop=True)

if df.empty:
    st.warning("Nessun evento live disponibile.")
    st.stop()

# =============== PREPROCESSING DI BASE ===============
df = df.fillna("")

# -- Calcolo tempo reale --
if "posizione" in df.columns:
    df["posizione"] = pd.to_numeric(df["posizione"], errors="coerce")
    df = df.sort_values(by="posizione")



# =============== GOL SEGNATI ===============
st.subheader("⚽ Gol")
df_gol = df[(df['evento'] == 'Gol')]

if df_gol.empty:
    st.info("Nessun gol segnato.")
else:
    # Calcolo risultato live
    gol_fatti = len(df_gol[df_gol['squadra'] != 'Loro'])
    gol_subiti = len(df_gol[df_gol['squadra'] == 'Loro'])
    risultato = f"{gol_fatti} - {gol_subiti}"

    # Mostra risultato
    st.markdown(f"### 🟢 Risultato Live: **Noi {risultato} Loro**")

    # Mostra tabella gol
    st.dataframe(df_gol[['chi', 'squadra', 'posizione']], use_container_width=True)



# =============== GRAFICI TIRI ===============
if "evento" in df.columns and "dove" in df.columns and "squadra" in df.columns:
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Tiri per Zona - Noi")
        fig_noi = plot_tiri_per_zona(df, squadra='Noi')
        st.pyplot(fig_noi, use_container_width=True)

    with col2:
        st.subheader("Tiri Subiti per Zona - Loro")
        fig_loro = plot_tiri_per_zona(df, squadra='Loro')
        st.pyplot(fig_loro, use_container_width=True)



