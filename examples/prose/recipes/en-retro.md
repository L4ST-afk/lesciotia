# Postmortem (English fixture)

Data pipeline went down for six hours last Wednesday. Root cause was not the network: the edge
box filled its disk, the process kept running, nothing was written, and no alert fired.
We only monitored liveness. Lesson: monitor the write path, not the service. Action: disk watermark
alert, owner Zhou, verify next Friday.
