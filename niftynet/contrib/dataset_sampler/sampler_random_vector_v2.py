# -*- coding: utf-8 -*-
"""
Generating sample arrays from random distributions.
"""
from __future__ import absolute_import, print_function, division

import numpy as np
import tensorflow as tf

from niftynet.engine.image_window import \
    N_SPATIAL, LOCATION_FORMAT, ImageWindow
from niftynet.contrib.dataset_sampler.image_window_dataset import \
    ImageWindowDataset
from niftynet.layer.base_layer import Layer


class RandomVectorSampler(Layer, ImageWindowDataset):
    """
    This class generates two samples from the standard normal
    distribution.  These two samples are mixed with n
    mixing coefficients. The coefficients are generated
    by ``np.linspace(0, 1, n_interpolations)``
    """

    def __init__(self,
                 names=('vector',),
                 vector_size=(100,),
                 batch_size=10,
                 n_interpolations=10,
                 mean=0.0,
                 stddev=1.0,
                 repeat=1,
                 queue_length=10,
                 name='random_vector_sampler'):
        # repeat=None for infinite loops
        Layer.__init__(self, name=name)

        self.n_interpolations = max(n_interpolations, 1)
        self.mean = mean
        self.stddev = stddev
        self.repeat = repeat
        self.names = names

        ImageWindowDataset.__init__(
            self,
            image_names={names[0]:(names[0],)},
            image_shapes={names[0]: vector_size},
            image_dtypes={names[0]: tf.float32},
            window_sizes={names[0]: {'spatial_window_size': vector_size}},
            batch_size=batch_size,
            n_subjects=1,
            queue_length=queue_length,
            from_generator=True,
            shuffle=False)
        self.window = ImageWindow(names=tuple({names[0]: vector_size}),
                                  shapes={names[0]: vector_size},
                                  dtypes={names[0]: tf.float32})
        self.window.n_samples = batch_size
        tf.logging.info("initialised sampler output %s ", self.window.shapes)

    def layer_op(self):
        """
        This function first draws two samples, and interpolates them
        with self.n_interpolations mixing coefficients.

        Location coordinates are set to ``np.ones`` for all the vectors.
        """
        total_iter = self.repeat if self.repeat is not None else 1
        while total_iter > 0:
            total_iter = total_iter - 1 if self.repeat is not None else 1
            embedding_x = np.random.normal(
                self.mean,
                self.stddev,
                *self.window.shapes[self.window.names[0]][1:])
            embedding_y = np.random.normal(
                self.mean,
                self.stddev,
                *self.window.shapes[self.window.names[0]][1:])
            steps = np.linspace(0, 1, self.n_interpolations)
            for (_, mixture) in enumerate(steps):
                output_vector = \
                    embedding_x * mixture + embedding_y * (1 - mixture)
                coordinates = np.ones((N_SPATIAL * 2 + 1), dtype=np.int32)
                output_dict = {}
                for name in self.window.names:
                    coordinates_key = LOCATION_FORMAT.format(name)
                    image_data_key = name
                    output_dict[coordinates_key] = coordinates
                    output_dict[image_data_key] = output_vector
                yield output_dict
