#include <string>
#include "model.h"

#include <TensorFlowLite_ESP32.h>
#include "tensorflow/lite/experimental/micro/kernels/all_ops_resolver.h"
#include "tensorflow/lite/experimental/micro/micro_error_reporter.h"
#include "tensorflow/lite/experimental/micro/micro_interpreter.h"
#include "tensorflow/lite/schema/schema_generated.h"
#include "tensorflow/lite/version.h"

namespace {
    tflite::ErrorReporter* error_reporter = nullptr;

    const tflite::Model* model = nullptr;

    tflite::MicroInterpreter* interpreter = nullptr;

    TfLiteTensor* input = nullptr;
    TfLiteTensor* output = nullptr;

    // store size as MB, KB, Byte trio
    constexpr int BYTES[] = {4, 0, 0};

    constexpr int kTensorArenaSize = BYTES[0] * 1024 * 1024 + BYTES[1] * 1024 + BYTES[2];

    uint8_t *tensor_arena = nullptr;
}  // namespace

const int NUM_CLASSES = 7;
const char *CLASSES[] = {"look_down", "look_left", "look_right", "look_up", "none", "tilt_left", "tilt_right"};

const float MIN_VALUE = -1000;
const float MAX_VALUE = 1000;

constexpr int INPUT_SHAPE[] = {100, 6};
constexpr int INPUT_SIZE = INPUT_SHAPE[0] * INPUT_SHAPE[1];

int argmax(float predictions[]) {
    int     max_index = 0;
    float   max_value = predictions[0];
    for (int i = 1; i < NUM_CLASSES; i++) {
        if (predictions[i] > max_value) {
            max_index = i;
            max_value = predictions[i];
        }
    }
    return max_index;
}

const char* output_class(float predictions[]) {
    return CLASSES[argmax(predictions)];
}

float randomFloat(float min, float max) {
    return min + (max - min) * (float)random(0, 10000) / 10000.0;
}

void print_shape(TfLiteTensor *tensor) {
    TfLiteIntArray *dims = tensor->dims;
    size_t size = dims->size;
    int* data = dims->data;

    if (size < 1) {
        Serial.println("Empty tensor");
        return;
    }

    std::string buffer = "(";
    for (int i = 0; i < size - 1; i++) {
        buffer += std::to_string(data[i]) + ", ";
    }
    buffer += std::to_string(data[size - 1]) + ")";
    Serial.println(buffer.c_str());
}

void setup() {
    Serial.begin(115200);
    
    static tflite::MicroErrorReporter micro_error_reporter;
    error_reporter = &micro_error_reporter;

    model = tflite::GetModel(model_tflite);
    if (!model) {
        Serial.println("Cannot get model");
        return;
    }

    if (model->version() != TFLITE_SCHEMA_VERSION) {
        error_reporter->Report(
            "Model provided is schema version %d not equal "
            "to supported version %d.",
            model->version(), TFLITE_SCHEMA_VERSION);
        Serial.println("Schema unsupported");
        return;
    }

    Serial.println("Model loaded successfully");

    tensor_arena = (uint8_t*)heap_caps_malloc(kTensorArenaSize + 16,
                               MALLOC_CAP_SPIRAM | MALLOC_CAP_8BIT);
    if (!tensor_arena) {
        error_reporter->Report("tensor_arena alloc failed");
        Serial.println("tensor_arena alloc failed");
        return;
    }

    static tflite::ops::micro::AllOpsResolver resolver;

    static tflite::MicroInterpreter static_interpreter(
        model, 
        resolver, 
        tensor_arena, 
        kTensorArenaSize, 
        error_reporter);
    interpreter = &static_interpreter;

    Serial.println("Interpreter instantiated successfully");

    TfLiteStatus allocate_status = interpreter->AllocateTensors();
    if (allocate_status != kTfLiteOk) {
        error_reporter->Report("AllocateTensors() failed");
        return;
    }

    Serial.println("Allocated tensors");

    input = interpreter->input(0);
    if (!input) {
        Serial.println("Input was not properly allocated");
        return;
    }

    Serial.print("Input tensor shape: ");
    print_shape(input);

    output = interpreter->output(0);
    if (!output) {
        Serial.println("Output was not properly allocated");
        return;
    }

    Serial.print("Output tensor shape: ");
    print_shape(output);

    Serial.println("Allocated tensors successfully");
}

void loop() {
    delay(1000);
}