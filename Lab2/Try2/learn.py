import argparse

ap = argparse.ArgumentParser()

ap.add_argument(
    "-e",
    "--epochs",
    required=True,
    help="number of epochs to train for",
    type=int,
)
ap.add_argument(
    "-r",
    "--learning-rate",
    required=False,
    help="learning rate for optimizer",
    default=0.00001,
    type=float,
)
ap.add_argument(
    "-b",
    "--batch-size",
    required=False,
    help="batch size for training (should be a power of 2)",
    default=32,
    type=int
)
ap.add_argument(
    "-l",
    "--load-checkpoint-path",
    required=False,
    help="checkpoint to load model weights from",
    default=None,
)
ap.add_argument(
    "-c",
    "--checkpoint-save-path",
    required=False,
    help="location to save model checkpoint to after every epoch",
    default=None,
)
ap.add_argument(
    "-f",
    "--frequency-checkpoint",
    required=False,
    help="frequency of saving model checkpoint (in epochs)",
    default=1,
    type=int
)
ap.add_argument(
    "-m",
    "--model",
    required=False,
    help="base model to use",
    choices=["mobilenet_v3", "resnet50"],
    default="mobilenet_v3",
)
ap.add_argument(
    "-s",
    "--save-path",
    required=False,
    help="location to save model after training",
    default=None,
)
ap.add_argument(
    "-p",
    "--plot-history-save-path",
    required=False,
    help="path (.json) to save training history to (will append if file exists)",
    default=None,
)

args = vars(ap.parse_args())
print(f"\n{args=}\n")
# ---------------------------------------------------------------------------- #


# ---------------------------------------------------------------------------- #
import time
import tensorflow as tf
import tensorflow.keras as keras
import tensorflow.keras.utils as utils
import tensorflow.keras.layers as layers
import tensorflow.keras.losses as losses
import tensorflow.keras.optimizers as optimizers


if args["model"] == "mobilenet_v3":
    import tensorflow.keras.applications as applications
    import tensorflow.keras.applications.mobilenet_v3 as mobilenet_v3

    preprocess_input = mobilenet_v3.preprocess_input
    create_model = applications.MobileNetV3Large
else:
    import tensorflow.keras.applications.resnet50 as resnet50

    preprocess_input = resnet50.preprocess_input
    create_model = resnet50.ResNet50


print(f"\n\nTensorflow version: {tf.__version__}")
# ---------------------------------------------------------------------------- #


# ---------------------------------------------------------------------------- #
print("\nLoading data...")

DATA_FOLDER = "datasetModified2"

seed = time.time_ns() & 0xfffffff

train, validation = utils.image_dataset_from_directory(
    DATA_FOLDER,
    label_mode='categorical',
    image_size=(224, 224),
    seed=seed,
    validation_split=0.2,
    subset='both',
)

train = train.map(lambda x, y: (preprocess_input(x), y))
validation = validation.map(lambda x, y: (preprocess_input(x), y))

print(f"{train=}")
print(f"{validation=}")
# ---------------------------------------------------------------------------- #


# ---------------------------------------------------------------------------- #
print("\nCreating model...")

base_model = create_model(
    include_top=True,
    weights='imagenet',
    # input_shape=(224, 224),
    # classifier_activation="softmax"
)

base_model.trainable = False

inputs = keras.Input(shape=(224, 224, 3))
outputs = base_model(inputs)
outputs = layers.Dense(3, activation="softmax")(outputs)

optimizer = optimizers.Adam(learning_rate = args["learning_rate"])

loss = losses.CategoricalCrossentropy()

model = keras.Model(inputs, outputs)
model.compile(
    optimizer = optimizer,
    loss = loss,
    metrics = ['accuracy']
)

if args["load_checkpoint_path"] is not None:
    model.load_weights(args["load_checkpoint_path"])

print(f"{base_model=}")
print(f"{inputs=}")
print(f"{outputs=}")
print(f"{optimizer=}")
print(f"{loss=}")
print(f"{model=}")
# ---------------------------------------------------------------------------- #


# ---------------------------------------------------------------------------- #
print("\nTraining model...")

if args["checkpoint_save_path"] is not None:
    if args["frequency_checkpoint"] == 1:
        save_freq = 'epoch'
    else:
        num_batches = len(train)
        save_freq = args["frequency_checkpoint"] * num_batches

    save_callback = keras.callbacks.ModelCheckpoint(
        filepath = args["checkpoint_save_path"],
        monitor = "val_accuracy",
        verbose = 1,
        save_weights_only = True,
        save_freq = save_freq,
    )
    callbacks = [save_callback]
else:
    callbacks = []

history = model.fit(
    train,
    batch_size = args["batch_size"],
    epochs = args["epochs"],
    verbose = 1,
	callbacks = callbacks,
    validation_data = validation,
    validation_batch_size = args["batch_size"]
)

print(f"Training finished.")

if args["save_path"] is not None:
    print(f"Saving model to {args['save_path']}")
    model.save(args["save_path"])
# ---------------------------------------------------------------------------- #


# ---------------------------------------------------------------------------- #
if args["plot_history_save_path"]:
    import json
    print(f"Saving training history to {args['plot_history_save_path']}")

    old_history = {
        "accuracy": [],
        "loss": [],
        "val_accuracy": [],
        "val_loss": [],
    }
    try:
        with open(args["plot_history_save_path"], "r") as f:
            old_history = json.load(f)
    except (FileNotFoundError, json.decoder.JSONDecodeError):
        pass

    if old_history is not None:
        old_history["accuracy"] += history.history["accuracy"]
        old_history["loss"] += history.history["loss"]
        old_history["val_accuracy"] += history.history["val_accuracy"]
        old_history["val_loss"] += history.history["val_loss"]

    with open(args["plot_history_save_path"], "w") as f:
        json.dump(old_history, f, indent=4)
# ---------------------------------------------------------------------------- #