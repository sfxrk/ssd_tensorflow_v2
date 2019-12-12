from import_keras import Input, Conv2D, MaxPooling2D, ZeroPadding2D, GlobalAveragePooling2D, Flatten, BatchNormalization, Dense, Reshape, concatenate, K, Activation, Model
import tensorflow as tf
from toolkit import PriorBox, Normalize


def ssd(width, height, channels, classes_num):
    net = {}
    # Input Layer
    net['input'] = Input(shape=(height, width, channels))
    # Block 1
    net['conv1_1'] = Conv2D(64, kernel_size=(3, 3), activation='relu', padding='same', name='conv1_1')(net['input'])
    net['conv1_2'] = Conv2D(64, kernel_size=(3, 3), activation='relu', padding='same', name='conv1_2')(net['conv1_1'])
    net['pool1'] = MaxPooling2D((2, 2), strides=(2, 2), padding='same', name='pool1')(net['conv1_2'])

    # Block 2
    net['conv2_1'] = Conv2D(128, kernel_size=(3, 3), activation='relu', padding='same', name='conv2_1')(net['pool1'])
    net['conv2_2'] = Conv2D(128, kernel_size=(3, 3), activation='relu', padding='same', name='conv2_2')(net['conv2_1'])
    net['pool2'] = MaxPooling2D((2, 2), strides=(2, 2), padding='same', name='pool2')(net['conv2_2'])

    # Block 3
    net['conv3_1'] = Conv2D(256, kernel_size=(3, 3), activation='relu', padding='same', name='conv3_1')(net['pool2'])
    net['conv3_2'] = Conv2D(256, kernel_size=(3, 3), activation='relu', padding='same', name='conv3_2')(net['conv3_1'])
    net['conv3_3'] = Conv2D(256, kernel_size=(3, 3), activation='relu', padding='same', name='conv3_3')(net['conv3_2'])
    net['pool3'] = MaxPooling2D((2, 2), strides=(2, 2), padding='same', name='pool3')(net['conv3_3'])

    # Block 4
    net['conv4_1'] = Conv2D(512, kernel_size=(3, 3), activation='relu', padding='same', name='conv4_1')(net['pool3'])
    net['conv4_2'] = Conv2D(512, kernel_size=(3, 3), activation='relu', padding='same', name='conv4_2')(net['conv4_1'])
    net['conv4_3'] = Conv2D(512, kernel_size=(3, 3), activation='relu', padding='same', name='conv4_3')(net['conv4_2'])
    net['pool4'] = MaxPooling2D((2, 2), strides=(2, 2), padding='same', name='pool4')(net['conv4_3'])

    # Block 5
    net['conv5_1'] = Conv2D(512, kernel_size=(3, 3), activation='relu', padding='same', name='conv5_1')(net['pool4'])
    net['conv5_2'] = Conv2D(512, kernel_size=(3, 3), activation='relu', padding='same', name='conv5_2')(net['conv5_1'])
    net['conv5_3'] = Conv2D(512, kernel_size=(3, 3), activation='relu', padding='same', name='conv5_3')(net['conv5_2'])
    net['pool5'] = MaxPooling2D((3, 3), strides=(1, 1), padding='same', name='pool5')(net['conv5_3'])

    # FC6
    net['fc6'] = Conv2D(1024, kernel_size=(3, 3), dilation_rate=(6, 6), activation='relu', padding='same', name='fc6')(net['pool5'])
    # x = Dropout(0.5, name='drop6')(x)

    # FC7
    net['fc7'] = Conv2D(1024, kernel_size=(1, 1), activation='relu', padding='same', name='fc7')(net['fc6'])
    # x = Dropout(0.5, name='drop7')(x)

    # Block 6
    net['conv6_1'] = Conv2D(256, kernel_size=(1, 1), activation='relu', padding='same', name='conv6_1')(net['fc7'])
    net['conv6_2'] = Conv2D(512, kernel_size=(3, 3), strides=(2, 2), activation='relu', padding='same', name='conv6_2')(net['conv6_1'])

    # Block 7
    net['conv7_1'] = Conv2D(128, kernel_size=(1, 1), activation='relu', padding='same', name='conv7_1')(net['conv6_2'])
    net['conv7_2'] = ZeroPadding2D()(net['conv7_1'])
    net['conv7_2'] = Conv2D(256, kernel_size=(3, 3), strides=(2, 2), activation='relu', padding='valid', name='conv7_2')(net['conv7_2'])

    # Block 8
    net['conv8_1'] = Conv2D(128, kernel_size=(1, 1), activation='relu', padding='same', name='conv8_1')(net['conv7_2'])  # TODO
    net['conv8_2'] = Conv2D(256, kernel_size=(3, 3), strides=(2, 2), activation='relu', padding='same', name='conv8_2')(net['conv8_1'])

    # Last Pool
    net['pool6'] = GlobalAveragePooling2D(name='pool6')(net['conv8_2'])

    # Prediction from conv4_3

    scale = 20
    net['conv4_3_norm'] = BatchNormalization(axis=3, epsilon=1e-6, scale=scale, gamma_initializer="ones", name='conv4_3_norm')(net['conv4_3'])
    # net['conv4_3_norm'] = Normalize(20, name='conv4_3_norm')(net['conv4_3'])
    num_priors = 3
    net['conv4_3_norm_mbox_loc'] = Conv2D(num_priors * 4, kernel_size=(3, 3), padding='same', name='conv4_3_norm_mbox_loc')(net['conv4_3_norm'])
    net['conv4_3_norm_mbox_loc_flat'] = Flatten(name='conv4_3_norm_mbox_loc_flat')(net['conv4_3_norm_mbox_loc'])

    net['conv4_3_norm_mbox_conf'] = Conv2D(num_priors * classes_num, kernel_size=(3, 3), padding='same', name='conv4_3_norm_mbox_conf')(net['conv4_3_norm'])
    net['conv4_3_norm_mbox_conf_flat'] = Flatten(name='conv4_3_norm_mbox_conf_flat')(net['conv4_3_norm_mbox_conf'])

    net['conv4_3_norm_mbox_priorbox'] = PriorBox((width, height), 30.0, aspect_ratios=[2], variances=[0.1, 0.1, 0.2, 0.2], name='conv4_3_norm_mbox_priorbox')(net['conv4_3_norm'])

    # Prediction from fc7

    num_priors = 6
    net['fc7_mbox_loc'] = Conv2D(num_priors * 4, kernel_size=(3, 3), padding='same', name='fc7_mbox_loc')(net['fc7'])
    net['fc7_mbox_loc_flat'] = Flatten(name='fc7_mbox_loc_flat')(net['fc7_mbox_loc'])
    net['fc7_mbox_conf'] = Conv2D(num_priors * classes_num, kernel_size=(3, 3), padding='same', name='fc7_mbox_conf')(net['fc7'])
    net['fc7_mbox_conf_flat'] = Flatten(name='fc7_mbox_conf_flat')(net['fc7_mbox_conf'])
    net['fc7_mbox_priorbox'] = PriorBox((width, height), 60.0, max_size=114.0, aspect_ratios=[2, 3], variances=[0.1, 0.1, 0.2, 0.2], name='fc7_mbox_priorbox')(net['fc7'])

    # Prediction from conv6_2

    num_priors = 6
    net['conv6_2_mbox_loc'] = Conv2D(num_priors * 4, kernel_size=(3, 3), padding='same', name='conv6_2_mbox_loc')(net['conv6_2'])
    net['conv6_2_mbox_loc_flat'] = Flatten(name='conv6_2_mbox_loc_flat')(net['conv6_2_mbox_loc'])
    net['conv6_2_mbox_conf'] = Conv2D(num_priors * classes_num, kernel_size=(3,3), padding='same', name='conv6_2_mbox_conf')(net['conv6_2'])
    net['conv6_2_mbox_conf_flat'] = Flatten(name='conv6_2_mbox_conf_flat')(net['conv6_2_mbox_conf'])
    net['conv6_2_mbox_priorbox'] = PriorBox((width, height), 114.0, max_size=168.0, aspect_ratios=[2, 3], variances=[0.1, 0.1, 0.2, 0.2], name='conv6_2_mbox_priorbox')(net['conv6_2'])

    # Prediction from conv7_2

    num_priors = 6
    net['conv7_2_mbox_loc'] = Conv2D(num_priors * 4, kernel_size=(3, 3), padding='same', name='conv7_2_mbox_loc')(net['conv7_2'])
    net['conv7_2_mbox_loc_flat'] = Flatten(name='conv7_2_mbox_loc_flat')(net['conv7_2_mbox_loc'])
    net['conv7_2_mbox_conf'] = Conv2D(num_priors * classes_num, kernel_size=(3,3), padding='same', name='conv7_2_mbox_conf')(net['conv7_2'])
    net['conv7_2_mbox_conf_flat'] = Flatten(name='conv7_2_mbox_conf_flat')(net['conv7_2_mbox_conf'])
    net['conv7_2_mbox_priorbox'] = PriorBox((width, height), 168.0, max_size=222.0, aspect_ratios=[2, 3], variances=[0.1, 0.1, 0.2, 0.2], name='conv7_2_mbox_priorbox')(net['conv7_2'])

    # Prediction from conv8_2
    num_priors = 6
    net['conv8_2_mbox_loc'] = Conv2D(num_priors * 4, kernel_size=(3,3), padding='same', name='conv8_2_mbox_loc')(net['conv8_2'])
    net['conv8_2_mbox_loc_flat'] = Flatten(name='conv8_2_mbox_loc_flat')(net['conv8_2_mbox_loc'])
    net['conv8_2_mbox_conf'] = Conv2D(num_priors * classes_num, kernel_size=(3,3), padding='same', name='conv8_2_mbox_conf')(net['conv8_2'])
    net['conv8_2_mbox_conf_flat'] = Flatten(name='conv8_2_mbox_conf_flat')(net['conv8_2_mbox_conf'])
    net['conv8_2_mbox_priorbox'] = PriorBox((width, height), 222.0, max_size=276.0, aspect_ratios=[2, 3], variances=[0.1, 0.1, 0.2, 0.2], name='conv8_2_mbox_priorbox')(net['conv8_2'])

    # Prediction from pool6
    num_priors = 6
    net['pool6_mbox_loc_flat'] = Dense(num_priors * 4, name='pool6_mbox_loc_flat')(net['pool6'])
    net['pool6_mbox_conf_flat'] = Dense(num_priors * classes_num, name='pool6_mbox_conf_flat')(net['pool6'])
    net['pool6_reshaped'] = Reshape((1, 1, 256), name='pool6_reshaped')(net['pool6'])
    net['pool6_mbox_priorbox'] = PriorBox((width, height), 276.0, max_size=330.0, aspect_ratios=[2, 3], variances=[0.1, 0.1, 0.2, 0.2], name='pool6_mbox_priorbox')(net['pool6_reshaped'])

    # Gather all predictions
    net['mbox_loc'] = concatenate([net['conv4_3_norm_mbox_loc_flat'],
                                   net['fc7_mbox_loc_flat'],
                                   net['conv6_2_mbox_loc_flat'],
                                   net['conv7_2_mbox_loc_flat'],
                                   net['conv8_2_mbox_loc_flat'],
                                   net['pool6_mbox_loc_flat']],
                                  axis=1, name='mbox_loc')
    net['mbox_conf'] = concatenate([net['conv4_3_norm_mbox_conf_flat'],
                                    net['fc7_mbox_conf_flat'],
                                    net['conv6_2_mbox_conf_flat'],
                                    net['conv7_2_mbox_conf_flat'],
                                    net['conv8_2_mbox_conf_flat'],
                                    net['pool6_mbox_conf_flat']],
                                   axis=1, name='mbox_conf')
    net['mbox_priorbox'] = concatenate([net['conv4_3_norm_mbox_priorbox'],
                                        net['fc7_mbox_priorbox'],
                                        net['conv6_2_mbox_priorbox'],
                                        net['conv7_2_mbox_priorbox'],
                                        net['conv8_2_mbox_priorbox'],
                                        net['pool6_mbox_priorbox']],
                                       axis=1, name='mbox_priorbox')

    num_boxes = net['mbox_loc'].shape[-1] // 4
    print(num_boxes)

    net['mbox_loc'] = Reshape((num_boxes, 4),
                              name='mbox_loc_final')(net['mbox_loc'])
    net['mbox_conf'] = Reshape((num_boxes, classes_num),
                               name='mbox_conf_logits')(net['mbox_conf'])
    net['mbox_conf'] = Activation('softmax',
                                  name='mbox_conf_final')(net['mbox_conf'])
    net['predictions'] = concatenate([net['mbox_loc'],
                               net['mbox_conf'],
                               net['mbox_priorbox']],
                               axis=2, name='predictions')
    model = Model(net['input'], net['predictions'])

    print('***model initiated***')
    return model


if __name__ == '__main__':  # TEST

    print("tensorflow-version:", tf.version.VERSION)
    print("tensorflow-compiler-version:", tf.version.COMPILER_VERSION)

    ssd(300, 300, 3, 1000)
