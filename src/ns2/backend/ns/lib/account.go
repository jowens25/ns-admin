package lib

import (
	"fmt"
	"log"
	"os/user"
	"slices"
	"strconv"
	"strings"
	"time"

	"github.com/godbus/dbus/v5"
)

var ADMIN_GROUP_NAME string = "nsadmin"
var USER_GROUP_NAME string = "nsuser"

//var ADMIN_GROUP

type MyUser struct {
	Username string `json:"Username"`
	Group    string `json:"Group"`
	Login    string `json:"Login"`
}

func (u *MyUser) FromDict(dict map[string]string) {

	u.Username = getString(dict, "Username")
	u.Group = getString(dict, "Group")
	u.Login = getString(dict, "Login")

}

func (u *MyUser) ToDict() map[string]string {

	res := map[string]string{}
	res["Username"] = u.Username
	res["Group"] = u.Group
	res["Login"] = u.Login

	return res

}

func RemoveUser(username string) error {
	if err := KillAllUserProcesses(username); err != nil {
		return err
	}
	return runCmd("userdel", username, "-rf")
}

func KillAllUserProcesses(username string) error {

	// ignoring errors here for now

	runCmd("pkill", "-KILL", "-u", username)

	return nil
}

func MakeNewAdmin(username string, password string) error {

	err := runCmd("useradd",

		"-N",
		"-g",
		"nsadmin",
		"-G",
		"nsuser,nsadmin",
		"--shell",
		"/bin/bash",
		"-m",
		username)

	if err != nil {
		return err
	}

	err = ChangePassword(username, password)

	if err != nil {
		return err
	}

	return nil

}

var defaultUsername string = "novus"
var defaultPassword string = "novus123"

func SetDefaultUser() error {

	_, err := user.Lookup(defaultUsername)
	if err == nil {
		// if found -> kill processes -> remove
		err := KillAllUserProcesses(defaultUsername)
		if err != nil {
			return err
		}

		err = RemoveUser(defaultUsername)
		if err != nil {
			return err
		}

	}
	// found or not found make a new one after clearing out old
	err = MakeNewAdmin(defaultUsername, defaultPassword)
	if err != nil {
		return err
	}

	return nil

}

func ChangePassword(username string, password string) error {

	// not found returns err
	_, err := user.Lookup(username)
	if err == nil {
		if err := KillAllUserProcesses(username); err != nil {
			return err
		}
	}

	in := fmt.Sprintf("%s:%s\n", username, password)

	err = runCmdWithStdin(in, "chpasswd")
	if err != nil {
		return err
	}
	return nil

}

func GetNumberOfAdmins() (int, error) {

	admins, err := getAdmins()

	if err != nil {
		return -1, err
	}

	return len(admins), nil

}

func IsAdmin(username string) (bool, error) {

	u, err := user.Lookup(username)
	if err != nil {
		return false, err
	}

	groups, err := u.GroupIds()
	if err != nil {
		return false, err
	}

	g, err := user.LookupGroup(ADMIN_GROUP_NAME)
	if err != nil {
		return false, err
	}

	if slices.Contains(groups, g.Gid) {
		return true, nil
	}
	return false, nil
}

func IsUser(username string) (bool, error) {

	u, err := user.Lookup(username)
	if err != nil {
		return false, err
	}

	groups, err := u.GroupIds()
	if err != nil {
		return false, err
	}

	g, err := user.LookupGroup(USER_GROUP_NAME)
	if err != nil {
		return false, err
	}

	if slices.Contains(groups, g.Gid) {
		return true, nil
	}
	return false, nil
}

// this needs to run as root...
func MakeNewUser(username string, password string) error {

	err := runCmd(
		"useradd",

		"-N",
		"-g",
		"nsuser",
		"-G",
		"nsuser",
		"--shell",
		"/bin/bash",
		"-m",
		username)

	if err != nil {
		return err
	}

	return ChangePassword(username, password)

}

func getAdmins() ([]string, error) {
	lines, err := GetFileLines("/etc/group")
	if err != nil {
		return []string{}, err
	}
	for _, line := range lines {
		if strings.HasPrefix(line, ADMIN_GROUP_NAME) {
			fields := strings.Split(line, ":")
			if len(fields[3]) > 0 {
				return strings.Split(strings.Trim(fields[3], "\n"), ","), nil
			}

		}
	}

	return nil, err
}

func getUsers() ([]string, error) {
	lines, err := GetFileLines("/etc/group")
	if err != nil {
		return nil, err
	}
	for _, line := range lines {
		if strings.HasPrefix(line, USER_GROUP_NAME) {
			fields := strings.Split(line, ":")

			if len(fields[3]) > 0 {
				return strings.Split(strings.Trim(fields[3], "\n"), ","), nil
			}

		}
	}

	return nil, err
}

func getUserAndAdmins() ([]MyUser, error) {
	users, err := getUsers()
	if err != nil {
		return nil, err
	}

	admins, err := getAdmins()
	if err != nil {
		return nil, err
	}
	var allUsers []MyUser

	if len(admins) > 0 {

		for _, a := range admins {
			idx := slices.Index(users, a)
			if idx != -1 {
				users = slices.Delete(users, idx, idx+1)
			}

			ll, err := GetLastLogin(a)
			if err != nil {
				fmt.Println(err.Error())
				return allUsers, err
			}

			allUsers = append(allUsers, MyUser{Group: "admin", Username: a, Login: ll})
		}
	}

	if len(users) > 0 {
		for _, u := range users {

			ll, err := GetLastLogin(u)
			if err != nil {
				fmt.Println(err.Error())

				return allUsers, err
			}

			allUsers = append(allUsers, MyUser{Group: "user", Username: u, Login: ll})

		}
	}

	return allUsers, nil
}

func ReadUserByUsername(username string) (*MyUser, error) {

	users, err := getUserAndAdmins()

	if err != nil {
		return nil, err
	}

	for _, u := range users {

		if u.Username == username {
			return &u, nil
		}
	}

	return nil, fmt.Errorf("user not found")

}

func ListAccounts() {

	accounts, err := getUserAndAdmins()
	if err != nil {
		fmt.Println(err.Error())
	}

	fmt.Println(len(accounts))

	for k, a := range accounts {
		fmt.Println(k, a)
	}

}

func GetLastLogin(username string) (string, error) {

	// Look up user by username
	u, err := user.Lookup(username)
	if err != nil {
		return "", fmt.Errorf("user.Lookup: %s", err.Error())
		//log.Printf("Could not find user: %s", err)
	}

	uid, err := strconv.ParseUint(u.Uid, 10, 32)

	if err != nil {
		return "", fmt.Errorf("strconv.ParseUint: %s", err.Error())
	}

	path, err := Call("org.freedesktop.login1", "/org/freedesktop/login1", "org.freedesktop.login1.Manager.GetUser", []any{uint32(uid)})
	if err != nil {
		return "Not logged in", nil
	}

	if p, ok := path.(dbus.ObjectPath); ok {
		ts, err := Call("org.freedesktop.login1", p, "org.freedesktop.DBus.Properties.Get", []any{"org.freedesktop.login1.User", "Timestamp"})

		if err != nil {

			return "", fmt.Errorf("Call -> GetProp: %s", err.Error())
		}

		ts64, _ := ts.(uint64)

		ts64 = ts64 / 1000000

		tm := time.Unix(int64(ts64), 0)

		log.Println(ts64)

		return fmt.Sprintf(tm.Format("2006-01-02 15:04:05")), nil
	}

	return "", fmt.Errorf("invalid path object")

}

// func RecordLogin(username string) error {
// 	u, err := user.Lookup(username)
// 	if err != nil {
// 		return fmt.Errorf("user.Lookup: %w", err)
// 	}

// 	uid, _ := strconv.ParseUint(u.Uid, 10, 32)
// 	gid, _ := strconv.ParseUint(u.Gid, 10, 32)

// 	conn, err := dbus.SystemBus()
// 	if err != nil {
// 		return fmt.Errorf("dbus.SystemBus: %w", err)
// 	}
// 	defer conn.Close()

// 	obj := conn.Object("org.freedesktop.login1", "/org/freedesktop/login1")

// 	// seat, vtnr, display can be empty for a headless/service session
// 	call := obj.Call(
// 		"org.freedesktop.login1.Manager.CreateSession",
// 		0,
// 		uint32(uid),       // uid
// 		uint32(0),         // pid (0 = caller)
// 		"ns",             // service name  ← your app
// 		"unspecified",     // type: "tty", "x11", "wayland", "unspecified"
// 		"user",            // class: "user", "greeter", "lock-screen"
// 		"",                // desktop
// 		"",                // seat id
// 		uint32(0),         // vtnr
// 		"",                // tty
// 		"",                // display
// 		false,             // remote
// 		"",                // remote user
// 		"",                // remote host
// 		[][]interface{}{}, // properties (empty slice)
// 	)

// 	if call.Err != nil {
// 		return fmt.Errorf("CreateSession: %w", call.Err)
// 	}

// 	// pull out the session id and path from the response
// 	var sessionId string
// 	var sessionPath dbus.ObjectPath
// 	if err := call.Store(&sessionId, &sessionPath); err != nil {
// 		return fmt.Errorf("Store: %w", err)
// 	}

// 	// immediately terminate it — logind has already stamped the timestamp
// 	sessionObj := conn.Object("org.freedesktop.login1", sessionPath)
// 	sessionObj.Call("org.freedesktop.login1.Session.Terminate", 0)

// 	return nil
// }

func TargetIsSender(target string, conn *dbus.Conn, sender dbus.Sender) (bool, error) {

	sendingUser, err := GetUserInfoFromSender(conn, sender)

	if err != nil {
		return false, err
	}

	targetUser, err := user.Lookup(target)

	if err != nil {
		return false, err
	}

	//log.Printf("TARGET: %s SENDING: %s RESULT: %b", targetUser.Uid, sendingUser.Uid, targetUser.Uid == sendingUser.Uid)

	return targetUser.Uid == sendingUser.Uid, nil

}

func TargetIsRoot(target string) (bool, error) {

	targetUser, err := user.Lookup(target)

	if err != nil {
		return false, err
	}

	return targetUser.Uid == "0", nil
}
