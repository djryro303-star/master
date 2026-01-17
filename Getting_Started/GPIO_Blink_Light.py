import RPi.GPIO as GPIO
import time

# Set up GPIO
GPIO.setmode(GPIO.BCM)  # Use BCM pin numbering
GPIO.setwarnings(False)

# Define GPIO pin for LED
LED_PIN = 5
LED_PIN2 = 20

# Set up the GPIO pins as outputs
GPIO.setup(LED_PIN, GPIO.OUT)
GPIO.setup(LED_PIN2, GPIO.OUT)

try:
    print("Blinking LED on GPIO07. Press Ctrl+C to stop...")
    while True:
        # Turn LED on
        GPIO.output(LED_PIN, GPIO.HIGH)
        GPIO.output(LED_PIN2, GPIO.HIGH)
        print("LED ON")
        time.sleep(1)  # Wait 1 second
        
        # Turn LED off
        GPIO.output(LED_PIN, GPIO.LOW)
        GPIO.output(LED_PIN2, GPIO.LOW)
        print("LED OFF")
        time.sleep(1)  # Wait 1 second

except KeyboardInterrupt:
    print("\nProgram stopped by user")

finally:
    # Clean up GPIO
    GPIO.cleanup()
    print("GPIO cleaned up")