package lib

import (
	"bufio"
	"encoding/json"
	"fmt"
	"os/exec"
	"strconv"
	"time"
)

type JournalEntry struct {
	Message           string `json:"MESSAGE"`
	SystemdUnit       string `json:"_SYSTEMD_UNIT"`
	RealtimeTimestamp string `json:"__REALTIME_TIMESTAMP"`
	Priority          string `json:"PRIORITY"`
}

// journalctl -b    -> current boot
// journalctl -b -1 -> previous boot
// journalctl -s "24 hours ago" --until "now"
// journalctl -s "7 days ago" --until "now"
// journalctl -p 0..x -> priority level emerg through 7 (debug)
// journalctl -u "identifier"

func FetchLogs(since string, priority int, units []string) ([]string, error) {
	args := []string{"-r", "-o", "json"}

	args = append(args, "--since", since, "--until", "now")

	if priority >= 0 && priority <= 7 {
		args = append(args, "-p", fmt.Sprintf("0..%d", priority))
	}

	for _, unit := range units {
		args = append(args, "-u", unit)
	}

	cmd := exec.Command("journalctl", args...)

	stdout, err := cmd.StdoutPipe()
	if err != nil {
		return nil, fmt.Errorf("failed to get stdout pipe: %w", err)
	}

	if err := cmd.Start(); err != nil {
		return nil, fmt.Errorf("failed to start journalctl: %w", err)
	}

	var messages []string
	scanner := bufio.NewScanner(stdout)
	for scanner.Scan() {
		var entry JournalEntry
		if err := json.Unmarshal(scanner.Bytes(), &entry); err != nil {
			continue
		}

		var formatted string
		if entry.RealtimeTimestamp != "" {
			if us, err := strconv.ParseInt(entry.RealtimeTimestamp, 10, 64); err == nil {
				t := time.Unix(us/1_000_000, (us%1_000_000)*1000)
				formatted = fmt.Sprintf("%s [%s] %s", t.Format("2006-01-02 15:04:05"), entry.SystemdUnit, entry.Message)
			}
		} else {
			formatted = entry.Message
		}

		messages = append(messages, formatted)
	}

	if err := cmd.Wait(); err != nil {
		return nil, fmt.Errorf("journalctl exited with error: %w", err)
	}

	return messages, nil

}
