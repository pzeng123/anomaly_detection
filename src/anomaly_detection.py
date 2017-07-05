import json
import sys
import time
from process_classes import User_Network, User


def main():
	# set file path, default first
	input_path = './log_input/batch_log.json'
	stream_path = './log_input/stream_log.json'
	output_path = './log_output/flagged_purchases.json'
	
	
	if len(sys.argv) == 4:
		input_path = sys.argv[1]
		stream_path = sys.argv[2]
		output_path = sys.argv[3]
	else: 
		print("input or output path error")

	## reads in the first file "batch_log.json" to build the initial user network.
	with open(input_path, "r") as batch_log:
		firstline = json.loads(batch_log.readline())
		D = int(firstline['D'])
		T = int(firstline['T'])

		# User_Network instance
		network = User_Network(D,T)

		# initialize first batch of events
		for nextline in batch_log:
			if nextline == '\n':
				continue
			event_log = json.loads(nextline)
			network.add_batch_event(event_log)

	print("loading complete")

	## reads in the second file "stream_log.json" as streaming events to determine the anomal purchases.
	with open(stream_path) as stream_log:
		with open(output_path, 'w') as flagged_purchases:
			for nextline in stream_log:
				if nextline == '\n':
					continue
				event_log = json.loads(nextline)
				anomal_string = network.add_streaming_event(event_log)
				# if there is anomal write it to output file
				if anomal_string:
					json.dump(anomal_string, flagged_purchases)
					flagged_purchases.write("\n")

	print("data stream analyze complete")


start_time = time.time()
main()
print("total time:" + "--- %s seconds ---" % (time.time() - start_time) )

