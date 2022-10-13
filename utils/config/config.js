/* MagicMirror² Config Sample
 *
 * By Michael Teeuw https://michaelteeuw.nl
 * MIT Licensed.
 *
 * For more information on how you can configure this file
 * see https://docs.magicmirror.builders/configuration/introduction.html
 * and https://docs.magicmirror.builders/modules/configuration.html
 */
let config = {
	address: "0.0.0.0", 	// Address to listen on, can be:
							// - "localhost", "127.0.0.1", "::1" to listen on loopback interface
							// - another specific IPv4/6 to listen on a specific interface
							// - "0.0.0.0", "::" to listen on any interface
							// Default, when address config is left out or empty, is "localhost"
	port: 8080,
	basePath: "/", 	// The URL path where MagicMirror² is hosted. If you are using a Reverse proxy
					// you must set the sub path here. basePath must end with a /
	ipWhitelist: [], 	// Set [] to allow all IP addresses
															// or add a specific IPv4 of 192.168.1.5 :
															// ["127.0.0.1", "::ffff:127.0.0.1", "::1", "::ffff:192.168.1.5"],
															// or IPv4 range of 192.168.3.0 --> 192.168.3.15 use CIDR format :
															// ["127.0.0.1", "::ffff:127.0.0.1", "::1", "::ffff:192.168.3.0/28"],

	useHttps: false, 		// Support HTTPS or not, default "false" will use HTTP
	httpsPrivateKey: "", 	// HTTPS private key path, only require when useHttps is true
	httpsCertificate: "", 	// HTTPS Certificate path, only require when useHttps is true

	language: "it",
	locale: "it-IT",
	logLevel: ["INFO", "LOG", "WARN", "ERROR"], // Add "DEBUG" for even more logging
	timeFormat: 24,
	units: "metric",
	// serverOnly:  true/false/'local' ,
	// local for armv6l processors, default
	//   starts serveronly and then starts chrome browser
	// false, default for all NON-armv6l devices
	// true, force serveronly mode, because you want to.. no UI on this device

	modules: [
		{
			module: 'alert',
			config: {}
		},
		{
			module: 'updatenotification',
			position: 'top_bar',
			config: {}
		},
		{
			module: 'clock',
			position: 'middle_center'
		},
		{
			module: 'calendar',
			header: 'US Holidays',
			position: 'top_left',
			config: {
				calendars: [
					{
						symbol: 'calendar-check',
						url: 'webcal://www.calendarlabs.com/ical-calendar/ics/76/US_Holidays.ics'
					}
				]
			}
		},
		{
			module: 'weather',
			header: 'Udine, IT',
			position: 'top_right',
			config: {
				weatherProvider: 'openweathermap',
				location: 'Udine,IT',
				locationID: 3165071,
				apiKey: 'f39667370750cfb8f5daebd19f0f1e29',
			}
		},
		{
			module: 'newsfeed',
			position: 'middle_center',
			config: {
				feeds: [
					{
						title: 'New York Times',
						url: 'https://rss.nytimes.com/services/xml/rss/nyt/HomePage.xml'
					}
				],
				showSourceTitle: true,
				showPublishDate: true,
				broadcastNewsFeeds: true,
				broadcastNewsUpdates: true
			}
		},
		{
			module: 'BIRTHDAYS',
			position: 'top_left',
			config: {
				limit:4,
				people:[
					{name:'Marco',birthdate:'1973-12-30'},
					{name:'Steve',birthdate:'1988-11-25'},
				]
			}
		},
		{
			module: 'MMM-page-indicator',
			position: 'bottom_bar',
			config: {
			  pages: 3,
			  activeBright: true,
			}
		},
		{
			module: 'MMM-pages',
			config: {
				// rotationTime: 10000, // 10 seconds
				modules: [
					[ 'updatenotification', 'clock'],
					[ 'weather', 'calendar', 'newsfeed' ],
					[ 'BIRTHDAYS' ]
				],
				fixed: [ 'MMM-page-indicator', 'MMM-Remote-Control', 'MMM-kalliope' ]
			}
		},
		{
			module: 'MMM-Remote-Control',
			config: {}
		},
		{
			module: 'MMM-kalliope',
			position: 'upper_third',
			config: {
				max: '4',
				title: 'Mycroft',
				keep_seconds: '0'
			}
		}
	]
};

/*************** DO NOT EDIT THE LINE BELOW ***************/
if (typeof module !== "undefined") {module.exports = config;}
