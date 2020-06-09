import tensorflow.compat.v2 as tf
import numpy as np
import matplotlib.pyplot as plt
class CVAE_Keras(tf.keras.Model):
    def __init__(self, latent_dim):
        super(CVAE_Keras, self).__init__()
        self.latent_dim = latent_dim
        self.inference_net = tf.keras.Sequential(
            [
                tf.keras.layers.InputLayer(input_shape=(84, 84, 3)),
                tf.keras.layers.Conv2D(filters=16, kernel_size=5, strides=(3, 3), activation='relu'),
                tf.keras.layers.Conv2D(filters=32, kernel_size=5, strides=(3, 3), activation='relu'),
                tf.keras.layers.Conv2D(filters=32, kernel_size=5, strides=(3, 3), activation='relu'),
                tf.keras.layers.Flatten(),
                # No activation
                tf.keras.layers.Dense(latent_dim + latent_dim),
            ]
        )
        '''print(len(self.inference_net.layers))
        print('infer the input shape is', self.inference_net.layers[0].get_input_shape_at(0))
        print('infer the output shape is', self.inference_net.layers[0].get_output_shape_at(0))
        print('infer the input shape is', self.inference_net.layers[1].get_input_shape_at(0))
        print('infer the output shape is', self.inference_net.layers[1].get_output_shape_at(0))
        print('infer the input shape is', self.inference_net.layers[2].get_input_shape_at(0))
        print('infer the output shape is', self.inference_net.layers[2].get_output_shape_at(0))
        print('infer the input shape is', self.inference_net.layers[3].get_input_shape_at(0))
        print('infer the output shape is', self.inference_net.layers[3].get_output_shape_at(0))
        print('infer the input shape is', self.inference_net.layers[4].get_input_shape_at(0))
        print('infer the output shape is', self.inference_net.layers[4].get_output_shape_at(0))'''

        self.generative_net = tf.keras.Sequential(
            [
                tf.keras.layers.InputLayer(input_shape=(latent_dim,)),
                tf.keras.layers.Dense(units=128, activation=tf.nn.relu),
                tf.keras.layers.Reshape(target_shape=(2,2,32)),
                tf.keras.layers.Conv2DTranspose(filters=32,kernel_size=5,strides=(3,3),padding='valid',activation='relu'),
                tf.keras.layers.Conv2DTranspose(filters=32,kernel_size=6,strides=(3, 3),padding='valid',activation='relu'),
                tf.keras.layers.Conv2DTranspose(filters=16, kernel_size=6, strides=(3, 3), padding='valid',activation='relu'),
                # No activation
                tf.keras.layers.Conv2DTranspose(filters=3, kernel_size=6, strides=(1, 1), padding="SAME"),
            ]
        )
        '''print(len(self.generative_net.layers))
        print('infer the input shape is', self.generative_net.layers[0].get_input_shape_at(0))
        print('infer the output shape is', self.generative_net.layers[0].get_output_shape_at(0))
        print('infer the input shape is', self.generative_net.layers[1].get_input_shape_at(0))
        print('infer the output shape is', self.generative_net.layers[1].get_output_shape_at(0))
        print('infer the input shape is', self.generative_net.layers[2].get_input_shape_at(0))
        print('infer the output shape is', self.generative_net.layers[2].get_output_shape_at(0))
        print('infer the input shape is', self.generative_net.layers[3].get_input_shape_at(0))
        print('infer the output shape is', self.generative_net.layers[3].get_output_shape_at(0))
        print('infer the input shape is', self.generative_net.layers[4].get_input_shape_at(0))
        print('infer the output shape is', self.generative_net.layers[4].get_output_shape_at(0))
        print('infer the input shape is', self.generative_net.layers[4].get_input_shape_at(0))
        print('infer the output shape is', self.generative_net.layers[4].get_output_shape_at(0))'''

    @tf.function
    def sample(self, eps=None):
        if eps is None:
            eps = tf.random.normal(shape=(100, self.latent_dim))
        return self.decode(eps, apply_sigmoid=True)

    def encode(self, x):
        mean, logvar = tf.split(self.inference_net(x), num_or_size_splits=2, axis=1)
        return mean, logvar

    def reparameterize(self, mean, logvar):
        eps = tf.random.normal(shape=mean.shape)
        return eps * tf.exp(logvar * .5) + mean

    def decode(self, z, apply_sigmoid=False):
        logits = self.generative_net(z)
        if apply_sigmoid:
            probs = tf.sigmoid(logits)
            return probs
        return logits

def log_normal_pdf(sample, mean, logvar, raxis=1):
    log2pi = tf.math.log(2. * np.pi)
    return tf.reduce_sum( -.5 * ((sample - mean) ** 2. * tf.exp(-logvar) + logvar + log2pi),axis=raxis)

@tf.function
def compute_loss(model, x):
    mean, logvar = model.encode(x)
    z = model.reparameterize(mean, logvar)
    x_logit = model.decode(z)
    cross_ent = tf.nn.sigmoid_cross_entropy_with_logits(logits=x_logit, labels=x)
    logpx_z = -tf.reduce_sum(cross_ent, axis=[1, 2, 3])
    logpz = log_normal_pdf(z, 0., 0.)
    logqz_x = log_normal_pdf(z, mean, logvar)
    return -tf.reduce_mean(logpx_z + logpz - logqz_x)

@tf.function
def compute_apply_gradients(model, x, optimizer):
    with tf.GradientTape() as tape:
        loss = compute_loss(model, x)
    gradients = tape.gradient(loss, model.trainable_variables)
    optimizer.apply_gradients(zip(gradients, model.trainable_variables))
    return loss

def generate_and_save_images(model, epoch, test_input):
    predictions = model.sample(test_input)
    fig = plt.figure(figsize=(4,4))

    for i in range(predictions.shape[0]):
        plt.subplot(4, 4, i+1)
        plt.imshow(predictions[i, :, :, 0], cmap='gray')
        plt.axis('off')

    # tight_layout minimizes the overlap between 2 sub-plots
    plt.savefig('image_at_epoch_{:04d}.png'.format(epoch))
    plt.show()