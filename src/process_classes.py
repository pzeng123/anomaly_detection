from datetime import datetime
import collections
import numpy as np
import heapq

class User_Network:

	def __init__(self, D, T):
		'''
		Initialize a User network object to check for anomalous purchases.

		D = number of degrees in User network to check
		T = number of historical purchases to check
		'''
		self.D = D
		self.T = T
		self.Userid = {}


	## Process individual events streaming in from input json file

	def add_batch_event(self, event_log):
		'''
		Add an batch event from the batch_log to User Network.
		
		event_log: Dictionary of parsed json purchase event.
		return: None
		'''
		event_type = event_log['event_type']
		if event_type == 'purchase':
			self.add_purchase(event_log)
		elif event_type == 'befriend':
			self.add_befriend(event_log)
		elif event_type == 'unfriend':
			self.add_unfriend(event_log)
		else:
			raise ValueError("Unknown event type", event_type)


	def add_streaming_event(self, event_log):
		'''
		Add in a streaming event from the stream log to this network.
		Check if this event is an anomalous purchase.

		event: Dictionary representing the parsed json event to add.
		return: an collections.OrderedDict representing an anomalous event if an anomaly
		is detected; boolean False otherwise.
		'''
		event_type = event_log['event_type']
		if event_type == 'purchase':
			self.add_purchase(event_log)
			id = event_log['id']
			amount = float(event_log['amount'])
			user = self.Userid[id]
			friends_list = self.get_friends_list(id)
			purchase_list = self.get_purchases(friends_list)
			if len(purchase_list) >= 2:
				amounts = [float(n) for _, _, n in purchase_list]
				mean = np.mean(amounts)
				std = np.std(amounts)
				if amount > mean + 3 * std:
					anomal_string = '{"event_type":"%s", "timestamp":"%s", "id": "%s", "amount": "%s", "mean": "%.2f", "sd": "%.2f"}\n' % (event_log["event_type"], event_log["timestamp"], event_log["id"], event_log["amount"], mean, std)
					return anomal_string
			return False
			
		elif event_type == 'befriend':
			self.add_befriend(event_log)
		elif event_type == 'unfriend':
			self.add_unfriend(event_log)
		else:
			raise ValueError("Event type error", event_type)


	## update network triggered by different events

	def add_purchase(self, event_log):
		'''
		Update network state with purchase event.

		event_log: Dictionary of parsed json representing purchase event.
		return: None
		'''
		# update user information
		id = event_log['id']
		timestamp = event_log['timestamp']
		amount = event_log['amount']
		
		# check this if id is old user or new user
		if id in self.Userid:
			user = self.Userid[id]
			user.purchase(timestamp, amount)
		else:
			new_user = User(id, self.T)
			new_user.purchase(timestamp,amount)
			self.Userid[id] = new_user
		return (timestamp,amount)


	def add_befriend(self, event_log):
		'''
		Update network state with befriend event.

		event_log: Dictionary of parsed json representing befriend event.
		return: None
		'''
		id1 = event_log['id1']
		id2 = event_log['id2']
		if id1 not in self.Userid:
			user1 = User(id1, self.T)
			self.Userid[id1] = user1
		else:
			user1 = self.Userid[id1]

		if id2 not in self.Userid:
			user2 = User(id2, self.T)
			self.Userid[id2] = user2
		else:
			user2 = self.Userid[id2]

		user1.friends.add(id2)
		user2.friends.add(id1)
		return user1, user2


	def add_unfriend(self, event_log):
		'''
		Update network state with unfriend event.

		event_log: Dictionary of parsed json representing unfriend event.
		return: None
		'''
		id1 = event_log['id1']
		id2 = event_log['id2']

		user1 = self.Userid[id1]
		user2 = self.Userid[id2]
		user1.friends.remove(id2)
		user2.friends.remove(id1)
		return user1, user2


	## get one user's friend list

	def get_friends_list(self, user):
		'''
		Gets the list of all friends in a user's dth degree network, where D is
		 defined by self.D, the degree of the network.

		user: integer id of user to get friends list from.
		return: list of all integer ids of people in user's dth degree network
		'''
		
		count = 0
		friends_list = set()
		queue = [(user, 0)]
		while queue != []:
			curr_user, depth = queue.pop(0)
			if curr_user not in friends_list:
				if depth < self.D+1:
					friends_list.add(curr_user)
					for friend in self.Userid[curr_user].friends:
						queue.append((friend,depth+1))
		friends_list.remove(user)
		return friends_list


	def get_purchases(self, friends_list):
		'''
		Gets the most recent purchases out of the users in friends_list,
		 where self.T is the number of purchases to consider.

		friends_list: a list of integer ids of users in the network.
		return: a list of tuples of (timestamp, rank, amount) for the T most
		 recent purchases in the network.
		'''
		p = []
		for friend in friends_list:
			p.extend(self.Userid[friend].purchases)
		return heapq.nlargest(self.T, p)

class User:
	def __init__(self, id, T):
		'''
		Initialize a User object.

		id = User id
		T = number of historical purchases to check
		'''
		self.id = id 
		self.friends = set() 
		self.purchases = collections.deque(maxlen=T) # list of tuples (timestamp, rank, amount)

	def purchase(self, timestamp, amount):
		'''
		User's purchase is stored as a tuple (timestamp, rank, amount).
		Rank is for the same timestamp purchases.

		timestamp, amount: from the original json event
		return: none
		'''

		ts = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
		if self.purchases:
			last_purchase = self.purchases[-1]
			last_purchase_ts = last_purchase[0]
			if ts == last_purchase_ts:
				last_purchase_rank = last_purchase[1]
				rank = last_purchase_rank + 1
			else:
				rank = 0
			new_purchase = (ts, rank, amount)
		else:
			new_purchase = (ts, 0, amount)
		self.purchases.append(new_purchase)

		


