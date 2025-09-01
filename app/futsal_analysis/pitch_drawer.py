import matplotlib.pyplot as plt
from matplotlib.patches import Arc, Circle, Rectangle

"""
This script generates a tactical representation of a futsal pitch using the Matplotlib library.
It was inspired by the mpl.soccer library.

The pitch measures 40 meters by 20 meters and includes features such as the outline, center circle, penalty spots, and penalty areas.
It also includes a class to plot a blind football pitch. In that case, the pitch dimensions are the same, but the features are adapted according to the sport.

"""

import matplotlib.pyplot as plt
from matplotlib.patches import Arc, Circle, Rectangle

class FutsalPitch:
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