from __future__ import print_function

import re
import struct
import sys
import time

class Pipes(object):

  word1 = ""
  word1complete = False
  word2 = ""
  word2complete = False
  msg = ""
  msgcomplete = False
  msg_read = 0
  msg_length = 0
  fifo = 0
  startedword = False
  confirmedword = False
  startedwordcount = 0

  def __init__(self):
    self.fifo = open(r'/tmp/myfifo', 'r+b', 0)

  def run(self):
    char = self.fifo.read(1)  # read a single character
    if char == "S":
      self.startedword = True
    if self.startedword and not self.confirmedword:
      self.startedwordcount = self.startedwordcount + 1
      if self.startedwordcount < 4 and char == "T":
        self.confirmedword = True
    if self.confirmedword and re.search("[\\a-zA-Z0-9.|]", char):
      #print (s, end='')
      # sys.stdout.flush()
      if self.word1complete:
        if self.word2complete:
          if self.msg_read < self.msg_length:
            self.msg = self.msg + char
            self.msg_read = self.msg_read + 1
          elif self.msg_read == self.msg_length:
            self.msgcomplete = True
        else:
          if char == "|":
            self.word2complete = True
            self.msg_length = int(self.word2) - 1
          else:
            self.word2 = self.word2 + char
      else:
        self.word1 = self.word1 + char
        if self.word1 == "START|":
          self.word1complete = True
        else:
          if self.word1 != "S" and self.word1 != "ST" and self.word1 != "STA" and self.word1 != "STAR" and self.word1 != "START":
            self.word1 = ""
            self.word1complete = False

  def reset_msg(self):
    self.word1 = ""
    self.word1complete = False
    self.word2 = ""
    self.word2complete = False
    self.msg = ""
    self.msg_read = 0
    self.msg_length = 0
    self.msgcomplete = False
    self.startedword = False
    self.confirmedword = False
    self.startedwordcount = 0
