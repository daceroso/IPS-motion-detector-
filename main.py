import os 
import sys 

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

import ips_protocol.recordings_pb2 as proto

recordings_proto = proto.Recording()


class IPSRecording:
    """Class to represent an IPS recording measurement.
    Parameters
    ----------
    pb_file : str 
        The absolute path of the recordings file in google protobuf format
    Attributes 
    ----------
    pb_file : str 
        The absolute path of the recordings file in google protobuf format
    positions : pd.DataFrame
        The ground truth position measurements as read from pb_file
    magnetics : pd.DataFrame
        The magnetics measurements as read from pb_file and calculated
        positions after magnetics_pos_cal() is called successfully
    rect_grid : np.array 
        Two dimensional array containing average magnetic value in the 
        grid defined by set_rect_grid
    cell_size : np.array
    Methods
    -------
    read_recording():
        Returns pandas DataFrames (positions and magnetics) based on pb_file
    magnetics_pos_calc():
        Calculates magnetics positions from ground truths via interpolation
    set_rect_grid(cell_size : list, plot : bool =True, cmap : str = 'hot')
        Calculates average magnetic measurements in a cell_size grid
    """

    def __init__(self, pb_file: str) -> None:
        """Initialize an IPSRecording instance. 
        Parameters
        ----------
        pb_file : str
            The absolute path of the recordings (google protobuf file)
        Returns
        -------
            None
        """

        if not os.path.isfile(pb_file):
            raise FileNotFoundError(f"The specified path {pb_file} isn't a proper file!")

        self.pb_file = pb_file
        self.read_recording()
        self.magnetics_pos_calc()    
                    
        return None

    def read_recording(self) -> list([pd.DataFrame, pd.DataFrame]):
        """Returns pd.DataFrames (positions and magnetics) from the pb_file.
        The structures of the DataFrames are:
            positions = pd.DataFrame('t', 'x', 'y', 'floor', 'type', 'accuracy')
            magnetics = pd.DataFrame('t', 'mx', 'my', 'mz', 'accuracy')
        NOTE: The pb & csv files notate magnetics values as 'x', 'y', 'z'!
        Parameters
        ----------
        None
        Returns
        -------
        positions : pd.DataFrame
            The pandas dataframe containing the ground truth positions.
        magnetics : pd.DataFrame
            The pandas dataframe containing the magnetics measurements.
        """

        with open(self.pb_file, 'rb') as f:
            file = f.read()
            # Deserialize binary based on the proto class "Recordings"
            measurements = recordings_proto.FromString(file)

        # Only the columns 't', 'x', 'y', 'z' are necessary!
        # The columns name 'must' be hardcoded (?)
        self.positions = pd.DataFrame(
            columns = ['t', 'x', 'y', 'floor', 'type', 'accuracy']
            )
        self.magnetics = pd.DataFrame(
            columns = ['t', 'mx', 'my', 'mz', 'accuracy']
            )

        # TODO: Maybe there is faster way?
        for i, position in enumerate(measurements.positions):
            self.positions.loc[i] = [
                position.t,
                position.x,
                position.y,
                position.floor,
                position.type,
                position.accuracy
                ]

        for j, magnetic in enumerate(measurements.magnetics):
            self.magnetics.loc[j] = [
                magnetic.t,
                magnetic.x,
                magnetic.y,
                magnetic.z,
                magnetic.accuracy
                ]

        # Renaming the columns of magnetics!
        self.magnetics.rename(columns = {'x': 'mx', 'y': 'my', 'z': 'mz'},
                             inplace=True)
        
        # Initialize the columns 'x' and 'y' -> positions to be calculated
        self.magnetics['x'] = 0.0
        self.magnetics['y'] = 0.0

        # NOTE: Discard magnetics measurements recorded after the last ground
        # truth measurement! Impossible to calculate their position!

        self.magnetics = self.magnetics[
                self.magnetics['t']<=self.positions['t'].max()
                ]


        return self.positions, self.magnetics

    def magnetics_pos_calc(self) -> None:
        """Calculates magnetic positions from ground truths via interpolation.
        
        The new columns are named 'x' and 'y' for position in x-axis and 
        y-axis respectively. The structure of magnetics DataFrame now is:
            magnetics = pd.DataFrame('t', 'mx', 'my', 'mz', 'mx',
                                    'accuracy', 'x', 'y')
        Parameters
        ----------
        None
        Returns
        -------
        None
        """
        
        tj = self.magnetics.loc[0]['t']
        row = 0

        for i in self.positions.index[:-1]:
            # Speed for routes between 2 consecutive ground truth positions
            # It is assumed CONST between consecutive ground truth positions
            speed_x = \
                (self.positions.loc[i+1]['x'] - self.positions.loc[i]['x']) /\
                (self.positions.loc[i+1]['t'] - self.positions.loc[i]['t'])

            speed_y = \
                (self.positions.loc[i+1]['y'] - self.positions.loc[i]['y']) /\
                (self.positions.loc[i+1]['t'] - self.positions.loc[i]['t'])

            # Calculate position for each magnetic in between i, i+1 ground 
            # truth positions. 
            # NOTE: We could assume constant time lapse for each measurement
            # and do this faster but it seems it is not exactly constant due
            # to rounding errors
            while tj < self.positions.loc[i+1]['t']:
                self.magnetics.loc[row,'x'] = (tj - self.positions.loc[i]['t']) * speed_x + self.positions.loc[i]['x']
                
                self.magnetics.loc[row,'y'] = (tj - self.positions.loc[i]['t']) * speed_y + self.positions.loc[i]['y']
                        
                row += 1

                # We exit the calculation as soon as we reach the end of the 
                # magnetics measurements or when the magnetics timestamp gets
                # greater positions.t.max() which we expect to never happen! 
                if row >= len(self.magnetics.index):
                    return None
                
                tj = self.magnetics.loc[row]['t']

        return None

    def set_rect_grid(self, cell_size: list,
                      plot: bool = True, cmap : str = 'hot') -> None:
        """Calculates average magnetic measurements in a cell_size grid.
        
        Parameters
        ----------
        cell_size : (n, m) array_like
            Two dimensional array containing the cell size (n, m) in 
            meters for the x-axis and y-axis respectively
        plot : bool
            If true it plots (matplotlib) a heatmap with the average 
            magnetic intensity of the cells
        cmap : str
            Matplotlib colormap. The default is 'hot' 
        Returns
        -------
        rect_grid : (N, M) np.array
            Two dimensional np.array of the average magnetic values 
            for each cell
        """

        self.cell_size = cell_size
        
        # I use positions instead of magnetics because they are far less
        # (faster to find min, max) and the calculation is still correct
        x_axis = [i for i in range(int(np.floor(self.positions.x.min())), 
                                  int(np.ceil(self.positions.x.max())),
                                  self.cell_size[0])
                                  ]
        y_axis = [i for i in range(int(np.floor(self.positions.y.min())),
                                  int(np.ceil(self.positions.y.max())),
                                  self.cell_size[1])
                                  ]

        # The average magnetic values per cell. This is returned
        self.rect_grid = np.zeros((len(x_axis) + 1, len(y_axis) + 1))
        # The number of magnetics encountered inside each cell
        cnt = np.zeros((len(x_axis) + 1, len(y_axis) + 1))

        x_min = self.positions.x.min()
        y_min = self.positions.y.min()

        # maxY = len(y_axis) 
        # maxX = len(x_axis)

        for _, magnetic in self.magnetics.iterrows():
            row = -int(np.ceil(magnetic['x'] - x_min) // self.cell_size[0]) 
            col = -int(np.ceil(magnetic['y'] - y_min) // self.cell_size[1])  

            self.rect_grid[row, col] += np.sqrt(pow(magnetic['mx'],2) 
                                                + pow(magnetic['my'],2)
                                                + pow(magnetic['mz'],2)
                                                )
                                                
                                        
            cnt[row, col] += 1

        # NOTE: to avoid runtime error division by zero add 1 to each zero cell
        cnt [cnt == 0] = np.NaN
        self.rect_grid = np.divide(self.rect_grid, cnt)
        
        if plot:
            plt.figure()
            plt.title(f'''Average magnetic value for recording 
            {os.path.basename(self.pb_file)} and 
            {self.cell_size[0]} x {self.cell_size[1]} rectangular grid'''
            )
            plt.imshow(self.rect_grid, cmap = cmap, origin = 'lower')
        
        return self.rect_grid


if __name__ == '__main__':
    PB_FILE = r'recordings_pb/10732.pb'
    ips1 = IPSRecording(os.path.join(os.getcwd(), PB_FILE))
    ips1.set_rect_grid([5,5])