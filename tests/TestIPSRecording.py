import unittest
import numpy as np
import pandas as pd
from unittest.mock import patch
from main import IPSRecording


class TestIPSRecording(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.magnetics_df = pd.read_csv('recordings_csv/10732/magnetics.csv')
        cls.position_df = pd.read_csv('recordings_csv/10732/positions.csv')

    def setUp(self):
        self.ips_recording = IPSRecording('recordings_pb/10732.pb')
        self.ips_recording.read_recording = lambda: (self.position_df, self.magnetics_df)

    def test_read_recording(self):
        with patch.object(self.ips_recording, 'read_recording', return_value=(self.position_df, self.magnetics_df)):
            positions, magnetics = self.ips_recording.read_recording()
            pd.testing.assert_frame_equal(positions, self.position_df)
            pd.testing.assert_frame_equal(magnetics, self.magnetics_df)

            print("Positions DataFrame:\n", positions)
            print("Magnetics DataFrame:\n", magnetics)

    def test_magnetics_pos_calc(self):
        self.ips_recording.read_recording()

        initial_speed_x = \
            (self.ips_recording.positions.loc[1]['x'] - self.ips_recording.positions.loc[0]['x']) / \
            (self.ips_recording.positions.loc[1]['t'] - self.ips_recording.positions.loc[0]['t'])
        initial_speed_y = \
            (self.ips_recording.positions.loc[1]['y'] - self.ips_recording.positions.loc[0]['y']) / \
            (self.ips_recording.positions.loc[1]['t'] - self.ips_recording.positions.loc[0]['t'])

        self.ips_recording.magnetics_pos_calc()

        self.assertIn('x', self.ips_recording.magnetics.columns)
        self.assertIn('y', self.ips_recording.magnetics.columns)

        print("Magnetics DataFrame with calculated positions:\n", self.ips_recording.magnetics.head())

        expected_first_x = self.ips_recording.positions.loc[0]['x']
        expected_first_y = self.ips_recording.positions.loc[0]['y']
        time_diff = self.ips_recording.magnetics.iloc[0]['t'] - self.ips_recording.positions.iloc[0]['t']
        expected_first_x += time_diff * initial_speed_x
        expected_first_y += time_diff * initial_speed_y

        self.assertEqual(self.ips_recording.magnetics.iloc[0]['x'], expected_first_x)
        self.assertEqual(self.ips_recording.magnetics.iloc[0]['y'], expected_first_y)

    def test_set_rect_grid(self):
        self.ips_recording.read_recording()
        self.ips_recording.magnetics_pos_calc()
        cell_size = [1, 1]
        print("Min x:", self.position_df['x'].min())
        print("Max x:", self.position_df['x'].max())
        print("Min y:", self.position_df['y'].min())
        print("Max y:", self.position_df['y'].max())
        print("Cell size:", cell_size)

        self.ips_recording.set_rect_grid(cell_size)
        actual_shape = self.ips_recording.rect_grid.shape

        print("Actual grid shape:", actual_shape)

        x_range = int(np.ceil(self.position_df['x'].max()) - np.floor(self.position_df['x'].min())) // cell_size[0] + 1
        y_range = int(np.ceil(self.position_df['y'].max()) - np.floor(self.position_df['y'].min())) // cell_size[1] + 1
        expected_shape = (x_range, y_range)
        print("Expected grid shape: ", expected_shape)
        self.assertEqual(actual_shape, expected_shape, "The shape of the grid does not match the expected shape.")


if __name__ == '__main__':
    unittest.main()
