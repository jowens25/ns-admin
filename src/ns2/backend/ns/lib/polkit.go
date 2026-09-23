package lib

import (
	"fmt"
	"log"
	"os"

	"github.com/godbus/dbus/v5"
)

func GetActionId(message dbus.Message) string {
	iface := message.Headers[dbus.FieldInterface].Value().(string)
	member := message.Headers[dbus.FieldMember].Value().(string)
	return fmt.Sprintf("%s.%s", iface, member)
}

type Subject struct {
	Kind    string                  `dbus:"subject_kind"`
	Details map[string]dbus.Variant `dbus:"subject_details"`
}

var DEBUG bool

// returns true of IsAuthorized
func CheckAuthorization(sender dbus.Sender, actionId string) bool {

	if DEBUG {
		return DEBUG
	}

	conn, err := dbus.SystemBus()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Failed to connect to system bus: %v\n", err)
		fmt.Printf("sys conn: %s\n", err.Error())
		return false
	}

	subject := Subject{
		Kind: "system-bus-name",
		Details: map[string]dbus.Variant{
			"name": dbus.MakeVariant(string(sender)),
		},
	}

	_, result, err := MakeDbusCall(conn,
		DbusCall{
			Destination: "org.freedesktop.PolicyKit1",
			Path:        "/org/freedesktop/PolicyKit1/Authority",
			Method:      "org.freedesktop.PolicyKit1.Authority.CheckAuthorization",
			Args: []any{
				subject,
				actionId,
				map[string]string{},
				uint(0),
				""}})

	if err != nil {
		log.Println(err.Error())
		fmt.Printf("make dbus call error: %s\n", err.Error())
	}

	//fmt.Println("NORMAL RETURN")

	u, err := GetUserInfoFromSender(conn, sender)
	if err != nil {
		fmt.Println(err.Error())
	}

	fmt.Println("Sender: ", u.Name)

	fmt.Println(result)

	slice, _ := result.([]any)
	return slice[0].(bool)
}

type Action struct {
	Action_id         string            `dbus:"action_id"`
	Description       string            `dbus:"description"`
	Message           string            `dbus:"message"`
	Vendor_name       string            `dbus:"vendor_name"`
	Vendor_url        string            `dbus:"vendor_url"`
	Icon_name         string            `dbus:"icon_name"`
	Implicit_any      uint32            `dbus:"implicit_any"`
	Implicit_inactive uint32            `dbus:"implicit_inactive"`
	Implicit_active   uint32            `dbus:"implicit_active"`
	Dict              map[string]string `dbus:"Dict"`
}

func EnumerateActions(sender dbus.Sender) ([]Action, error) {

	conn, err := dbus.SystemBus()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Failed to connect to system bus: %v\n", err)
		return []Action{}, err
	}

	_, result, err := MakeDbusCall(conn,
		DbusCall{
			Destination: "org.freedesktop.PolicyKit1",
			Path:        "/org/freedesktop/PolicyKit1/Authority",
			Method:      "org.freedesktop.PolicyKit1.Authority.EnumerateActions",
			Args:        []any{""},
		}) // empty locale

	actions := []Action{}
	for _, action := range result.([][]any) {

		actions = append(actions, Action{
			Action_id:         action[0].(string),
			Description:       action[1].(string),
			Message:           action[2].(string),
			Vendor_name:       action[3].(string),
			Vendor_url:        action[4].(string),
			Icon_name:         action[5].(string),
			Implicit_any:      action[6].(uint32),
			Implicit_inactive: action[7].(uint32),
			Implicit_active:   action[8].(uint32),
			Dict:              action[9].(map[string]string),
		})
	}

	return actions, nil

}
