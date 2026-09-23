package lib

import (
	"fmt"
	"log"

	"github.com/godbus/dbus/v5"
)

// AccountsInterface implements the com.novus.ns.accounts interface
type AccountInterface struct {
	conn *dbus.Conn
}

// get all users
// make admins
// make users
// delete users
// change password

func (a *AccountInterface) SetPasswordPolicy(policy map[string]any, sender dbus.Sender, message dbus.Message) *dbus.Error {

	if isAuthorized := CheckAuthorization(sender, GetActionId(message)); !isAuthorized {

		return &dbus.Error{
			Name: "org.freedesktop.DBus.Error.AccessDenied",
			Body: []any{"Not authorized to set password policy"},
		}

	}

	err := SetPolicy(policy)
	if err != nil {
		return &dbus.Error{
			Name: "org.freedesktop.DBus.Error",
			Body: []any{err.Error()},
		}

	}
	err = a.conn.Emit("/com/novus/ns", "com.novus.ns.accounts.Changed", "SetPasswordPolicy")
	if err != nil {
		log.Println(err.Error())
	}
	return nil

}

func (a *AccountInterface) GetPasswordPolicy() (map[string]any, *dbus.Error) {

	policy, err := GetPolicy()
	if err != nil {
		return nil, &dbus.Error{
			Name: "org.freedesktop.DBus.Error",
			Body: []any{err.Error()},
		}

	}

	return map[string]any{
		"max":    policy.MaxLength,
		"min":    policy.MinLength,
		"upper":  policy.RequireUppercase,
		"lower":  policy.RequireLowercase,
		"digit":  policy.RequireDigit,
		"symbol": policy.RequireSymbol,
	}, nil

}

func (a *AccountInterface) ValidatePassword(password string) (bool, *dbus.Error) {

	isValid, err := Validate(password)
	if err != nil {
		return false, &dbus.Error{
			Name: "org.freedesktop.DBus.Error",
			Body: []any{err.Error()},
		}

	}

	return isValid, nil

}

func (a *AccountInterface) UserExists(username string) *dbus.Error {

	usersAndAdmins, err := getUserAndAdmins()

	if err != nil {

		return &dbus.Error{
			Name: "org.freedesktop.DBus.Error",
			Body: []any{err.Error()},
		}
	}

	for _, u := range usersAndAdmins {
		if u.Username == username {
			return &dbus.Error{
				Name: "org.freedesktop.DBus.Error",
				Body: []any{"User exists"},
			}
		}
	}

	return nil

}

func (a *AccountInterface) AddUser(username string, password string, sender dbus.Sender, message dbus.Message) (string, *dbus.Error) {

	if isAuthorized := CheckAuthorization(sender, GetActionId(message)); !isAuthorized {

		return "", &dbus.Error{
			Name: "org.freedesktop.DBus.Error.AccessDenied",
			Body: []any{"Not authorized to add user"},
		}
	}

	err := MakeNewUser(username, password)
	if err != nil {
		return "", &dbus.Error{
			Name: "org.freedesktop.DBus.Error",
			Body: []any{err.Error()},
		}

	}

	err = a.conn.Emit("/com/novus/ns", "com.novus.ns.accounts.Changed", "AddUser")
	if err != nil {
		log.Println(err.Error())
	}

	return fmt.Sprintf("added %s", username), nil

}

func (a *AccountInterface) AddAdmin(username string, password string, sender dbus.Sender, message dbus.Message) (string, *dbus.Error) {

	if isAuthorized := CheckAuthorization(sender, GetActionId(message)); !isAuthorized {
		return "", &dbus.Error{
			Name: "org.freedesktop.DBus.Error.AccessDenied",
			Body: []any{"Not authorized to add admin"},
		}
	}

	err := MakeNewAdmin(username, password)
	if err != nil {
		return "", &dbus.Error{
			Name: "org.freedesktop.DBus.Error",
			Body: []any{err.Error()},
		}

	}
	err = a.conn.Emit("/com/novus/ns", "com.novus.ns.accounts.Changed", "AddAdmin")
	if err != nil {
		log.Println(err.Error())
	}

	return fmt.Sprintf("added %s", username), nil

}

func (a *AccountInterface) SetupDefaultUser(sender dbus.Sender, message dbus.Message) (string, *dbus.Error) {

	if isAuthorized := CheckAuthorization(sender, GetActionId(message)); !isAuthorized {
		return "", &dbus.Error{
			Name: "org.freedesktop.DBus.Error.AccessDenied",
			Body: []any{"Not authorized to setup default user"},
		}
	}

	err := SetDefaultUser()
	if err != nil {
		return "", &dbus.Error{
			Name: "org.freedesktop.DBus.Error",
			Body: []any{err.Error()},
		}

	}
	err = a.conn.Emit("/com/novus/ns", "com.novus.ns.accounts.Changed", "SetupDefaultUser")
	if err != nil {
		log.Println(err.Error())
	}

	return "reset complete", nil

}

func (a *AccountInterface) Remove(sender dbus.Sender, message dbus.Message, username string) (string, *dbus.Error) {

	if isAuthorized := CheckAuthorization(sender, GetActionId(message)); !isAuthorized {

		return "", &dbus.Error{
			Name: "org.freedesktop.DBus.Error.AccessDenied",
			Body: []any{"Not authorized to remove users"},
		}

	}

	// not going to let us delete ourselves
	isSender, err := TargetIsSender(username, a.conn, sender)
	if err != nil {
		return "", &dbus.Error{
			Name: "org.freedesktop.DBus.Error",
			Body: []any{err.Error()},
		}
	}

	isRoot, err := TargetIsRoot(username)
	if err != nil {
		return "", &dbus.Error{
			Name: "org.freedesktop.DBus.Error",
			Body: []any{err.Error()},
		}
	}

	if isRoot {
		return "", &dbus.Error{
			Name: "org.freedesktop.DBus.Error",
			Body: []any{"cannot delete root account"},
		}
	}

	if isSender {
		return "", &dbus.Error{
			Name: "org.freedesktop.DBus.Error",
			Body: []any{"cannot delete active account"},
		}

	}

	numAdmins, err := GetNumberOfAdmins()
	if err != nil {
		return "", &dbus.Error{
			Name: "org.freedesktop.DBus.Error",
			Body: []any{err.Error()},
		}

	}

	if isAdmin, err := IsAdmin(username); isAdmin {

		if err != nil {
			return "", &dbus.Error{
				Name: "org.freedesktop.DBus.Error",
				Body: []any{err.Error()},
			}
		}

		if numAdmins > 1 {
			err = RemoveUser(username)
			if err != nil {
				return "", &dbus.Error{
					Name: "org.freedesktop.DBus.Error",
					Body: []any{err.Error()},
				}

			}
			err = a.conn.Emit("/com/novus/ns", "com.novus.ns.accounts.Changed", "Remove")
			if err != nil {
				log.Println(err.Error())
			}
			return fmt.Sprintf("removed %s", username), nil

		} else {
			return "", &dbus.Error{
				Name: "org.freedesktop.DBus.Error",
				Body: []any{"cannot remove the last admin"},
			}

		}
	} else {

		err = RemoveUser(username)
		if err != nil {
			return "", &dbus.Error{
				Name: "org.freedesktop.DBus.Error",
				Body: []any{err.Error()},
			}

		}
		err = a.conn.Emit("/com/novus/ns", "com.novus.ns.accounts.Changed", "Remove")
		if err != nil {
			log.Println(err.Error())
		}
		return fmt.Sprintf("removed %s", username), nil

	}

}

func (a *AccountInterface) GetUsers() ([]map[string]string, *dbus.Error) {

	users := []map[string]string{}

	usersAndAdmins, err := getUserAndAdmins()

	if err != nil {

		return nil, &dbus.Error{
			Name: "org.freedesktop.DBus.Error",
			Body: []any{err.Error()},
		}
	}

	for _, u := range usersAndAdmins {
		users = append(users, u.ToDict())
	}

	return users, nil

}

func (a *AccountInterface) GetUserByUsername(username string) (map[string]string, *dbus.Error) {

	u, err := ReadUserByUsername(username)

	if err != nil {
		return nil, &dbus.Error{
			Name: "org.freedesktop.DBus.Error",
			Body: []any{err.Error()},
		}
	}

	return u.ToDict(), nil

}

func (a *AccountInterface) UpdatePassword(targetUsername string, newpassword string, sender dbus.Sender, message dbus.Message) (string, *dbus.Error) {

	caller, err := GetUserInfoFromSender(a.conn, sender)
	if err != nil {
		return "", &dbus.Error{
			Name: "org.freedesktop.DBus.Error",
			Body: []any{err.Error()},
		}
	}

	callerUsername := caller.Username

	if isAuthorized := CheckAuthorization(sender, GetActionId(message)); !isAuthorized {

		return "", &dbus.Error{
			Name: "org.freedesktop.DBus.Error.AccessDenied",
			Body: []any{"Not authorized to update passwords"},
		}
	}

	callerIsTarget, err := TargetIsSender(targetUsername, a.conn, sender)

	if err != nil {
		return "", &dbus.Error{
			Name: "org.freedesktop.DBus.Error",
			Body: []any{err.Error()},
		}
	}

	targetIsAdmin, err := IsAdmin(targetUsername)
	if err != nil {
		return "", &dbus.Error{
			Name: "org.freedesktop.DBus.Error",
			Body: []any{err.Error()},
		}
	}

	callerIsAdmin, err := IsAdmin(callerUsername)
	if err != nil {
		return "", &dbus.Error{
			Name: "org.freedesktop.DBus.Error",
			Body: []any{err.Error()},
		}
	}

	// caller wants to change their own password
	if callerIsTarget {

		err = ChangePassword(targetUsername, newpassword)
		if err != nil {
			return "", &dbus.Error{
				Name: "org.freedesktop.DBus.Error",
				Body: []any{err.Error()},
			}

		}
		err = a.conn.Emit("/com/novus/ns", "com.novus.ns.accounts.Changed", "UpdatePassword")
		if err != nil {
			log.Println(err.Error())
		}
		return "password updated", nil

		// otherwise someone else wants to change it

	} else if callerIsAdmin && !targetIsAdmin {

		err = ChangePassword(targetUsername, newpassword)
		if err != nil {
			return "", &dbus.Error{
				Name: "org.freedesktop.DBus.Error",
				Body: []any{err.Error()},
			}

		}
		err = a.conn.Emit("/com/novus/ns", "com.novus.ns.accounts.Changed", "UpdatePassword")
		if err != nil {
			log.Println(err.Error())
		}
		return "password updated", nil

	} else {

		return "", &dbus.Error{
			Name: "org.freedesktop.DBus.Error",
			Body: []any{"Not authorized to change this user's password"},
		}

	}

}
