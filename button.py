import RPi.GPIO as GPIO

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BOARD)
GPIO.setup(11, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

while GPIO.input(11) == GPIO.LOW:
	print("OFF")

print("ON")