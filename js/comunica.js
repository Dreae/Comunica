$(function(){
	String.prototype.htmlEncode = function(){
		var htmlEscapes = {
		  '&': '&amp;',
		  '<': '&lt;',
		  '>': '&gt;',
		  '"': '&quot;',
		  "'": '&#x27;',
		  '/': '&#x2F;'
		};
		var htmlEscaper = /[&<>"'\/]/g;
		return this.replace(htmlEscaper, function(match){return htmlEscapes[match]});
	};
});
(function($){
	$.fn.comunica = function(options){
		var settings = $.extend({height: 380,width: 310}, options)
		if(settings.width < 310){
			settings.width = 310;
		}
		if(settings.height < 380){
			settings.height = 380;
		}
		this.html($('<div class="comunica"></div>')
					.css({
					display: 'block', 
					height: settings.height - 8 + 'px', 
					width: settings.width - 8 + 'px'
				})
			.append($('<div id="comunica-chat-pane"></div>')
				.css({
					width: '100%',
					height: settings.height - 118 + 'px',
					'overflow-y': 'auto',
					'overflow-x': 'wrap',
					'word-wrap': 'break-word'
				})
			)
			.append($('<div class="comunica-controls"></div>')
				.css({
					width: settings.width - 16 + 'px',
					height: '110px'
				})
				.append($('<textarea class="comunica-msg-input" id="comunica-message-input"></textarea>')
					.focus($.fn.comunica.inputFocus)
					.keydown($.fn.comunica.inputKeyDown)
					.css({
						height: '60px',
						width: '100%'})
				)
				.append($('<a href="#" class="comunica-send-btn" id="comunica-send-message">Send</a>').click($.fn.comunica.sendClick))
				.append($('<button class="comunica-control-button" id="comunica-viewers"><span class="glyphicon glyphicon-list"></span></button>')
					.click($.fn.comunica.viewersClick)
				)
				.append($('<button class="comunica-control-button" id="comunica-settings"><span class="glyphicon glyphicon-cog"></span></button>')
					.click($.fn.comunica.settingsClick)
				)
			)
			.append($('<div class="comunica-drop-menu" id="comunica-settings-drop"></div>')
				.append($('<div class="colors"></div>')
					.append($('<br>'))
					.append($('<a class="color" style="background-color:#ff0000"></a>').click($.fn.comunica.setColor))
					.append($('<a class="color" style="background-color:#008000"></a>').click($.fn.comunica.setColor))
					.append($('<a class="color" style="background-color:#b22222"></a>').click($.fn.comunica.setColor))
					.append($('<a class="color" style="background-color:#ff7f50"></a>').click($.fn.comunica.setColor))
					.append($('<a class="color" style="background-color:#9acd32"></a>').click($.fn.comunica.setColor))
					.append($('<a class="color" style="background-color:#ff4500"></a>').click($.fn.comunica.setColor))
					.append($('<a class="color" style="background-color:#ff00ff"></a>').click($.fn.comunica.setColor))
					.append($('<a class="color" style="background-color:#2e8b57"></a>').click($.fn.comunica.setColor))
					.append($('<a class="color" style="background-color:#daa520"></a>').click($.fn.comunica.setColor))
					.append($('<a class="color" style="background-color:#ff69b4"></a>').click($.fn.comunica.setColor))
					.append($('<a class="color" style="background-color:#00ff00"></a>').click($.fn.comunica.setColor))
					.append($('<a class="color" style="background-color:#d2691e"></a>').click($.fn.comunica.setColor))
					.append($('<a class="color" style="background-color:#5f9ea0"></a>').click($.fn.comunica.setColor))
					.append($('<a class="color" style="background-color:#1e90ff"></a>').click($.fn.comunica.setColor))
					.append($('<a class="color" style="background-color:#0000ff"></a>').click($.fn.comunica.setColor))
					.append($('<a class="color" style="background-color:#ff69b4"></a>').click($.fn.comunica.setColor))
					.append($('<a class="color" style="background-color:#8a2be2"></a>').click($.fn.comunica.setColor))
					.append($('<a class="color" style="background-color:#00ff7f"></a>').click($.fn.comunica.setColor))
					.append($('<br>'))
					.append($('<p></p>')
						.append($('<input type="checkbox" id="comunica-timestamp-check">')
							.change(function(){
								$(this).comunica.timestamps = this.checked
							})
						)
						.append($('<span style="font-weight:300">Timestamps</span>'))
						.append($('<div class="about-comunica"></div>')
							.append($('<span class="about"><a href="https://github.com/Dreae/Comunica" target="_blank">Comunica</a></span>'))
						)
					)
				)
			)
			.append($('<div class="comunica-drop-menu" id="comunica-viewers-drop"></div>')
				.append($('<h2>Viewers</h2>'))
				.append($('<div class="loading" id="comunica-viewers-list"></div>'))
			)
			.append($('<div class="comunica-opaque-popup" id="comunica-pick-nickname-popup"></div>')
				.append($('<div class="comunica-pick-nick"></div>')
					.append($('<center></center>')
						.append($('<h3>Pick a name</h3>'))
						.append($('<input type="text" id="comunica-pick-nickname-input">'))
						.append($('<br><button id="comunica-save-nick">Save</button>')
							.click($.fn.comunica.saveNickClick)
						)
					)
				)
			).on('shown', function(){
				$('#comunica-pick-nickname-popup > .comunica-pick-nick').css({
					'margin-top': -$('#comunica-pick-nickname-popup > .comunica-pick-nick').height()/2
				});
			})
			.append($('<div class="comunica-opaque-popup" id="comunica-not-connected-popup"></div>')
				.append($('<div class="comunica-not-connected"></div>')
					.append($('<h2>Could not connect to chat room</h2>'))
					.append($('<h1><span class="web-glyphicon glyphicon-frown"></span></h1>'))
				)
			)
		);
		$('#comunica-pick-nickname-input').keydown(function(event){
			if(event.which == 13){
				event.preventDefault();
				$('#comunica-save-nick').click();
			}
		});
		$('body > div:not(#comunica, #comunica-viewers-drop, #comunica-settings-drop)').click($.fn.comunica.fadeDrops);
		this.comunica.nick = false;
		this.comunica.supports_auth = false;
	}
	$.fn.comunica.connect = function(host, room){
		this.host = host
		this.room = room
		if('MozWebSocket' in window)
		{
			WebSocket = MozWebSocket;
		}
		if('WebSocket' in window)
		{
			var ws_con = "ws://"+host+"/"+room;
			var ws = new WebSocket(ws_con, 'comunica');
			ws.onopen = this.connected;
			ws.onmessage = this.recvmsg;
			ws.onclose = this.connection_closed;
			ws.onerror = this.websock_error;
			this.ws = ws;
		}
	}
	$.fn.comunica.websock_error = function(error){
		console.log(error);
	}
	$.fn.comunica.send = function(msg){
		try {
			this.ws.send(msg);
		} 
		catch(ex){
			return false;
		}
	}
	$.fn.comunica.recvmsg = function(event){
		try{
			var json = JSON.parse(event.data);
		} catch (e) {
			console.log("Error parsing frame data: " + event.data);
			return;
		}
		if(json.evt == "message"){
			var timestamp = '';
			if($.fn.comunica.timestamps){
				var dt = new Date();
				var timestamp = (dt.getHours() < 10 ? '0' + dt.getHours() : dt.getHours()) + ':'
								+ (dt.getMinutes() < 10 ? '0' + dt.getMinutes() : dt.getMinutes());
			}
			$('#comunica-chat-pane').append('<p style="margin:0;">' + timestamp
									+ ' <span style="color:'+ json.from[1].htmlEncode()
									+ ';font-weight:600">' + json.from[0].htmlEncode() + '</span>: ' + json.value.htmlEncode() + '</p>');
			$('#comunica-chat-pane').animate({scrollTop: $('#comunica-chat-pane')[0].scrollHeight}, 300);
			if($('#comunica-chat-pane > p').length > 150){
				$('#comunica-chat-pane p:first-child').remove();
			}
		}
		else if(json.evt == "viewers"){
			var viewerList = $('<div class="comunica-viewer-list" id="comunica-viewers-list"></div>');
			json.value.forEach(function(name){
				if(name != null){
					viewerList.append('<p class="comunica-viewer">' + name + '</p>');
				}
			});
			$('#comunica-viewers-drop > #comunica-viewers-list').replaceWith(viewerList)
		}
		else if(json.evt == "server-info"){
			if(json.supports_auth){
				$('#comunica-settings-drop')
				.append($('<div name="comunica-login-form"></div>')
					.append($('<h3>Login</h3>'))
					.append($('<p class="comunica-login-form"></p>')
						.append($('<input name="comunica-login-username" placeholder="Username" type="text"/>'))
						.append($('<input name="comunica-login-password" placeholder="Password" type="password"/>'))
					)
				)
				$('#comunica-pick-nickname-popup > .comunica-pick-nick > center > #comunica-save-nick').remove()
				$('#comunica-pick-nickname-popup > .comunica-pick-nick > center')
				.append($('<div name="comunica-login-form"></div>')
					.append($('<p> - or - </p>'))
					.append($('<p>Login</p>'))
					.append($('<input name="comunica-login-username" placeholder="Username" type="text"/>'))
					.append($('<input name="comunica-login-password" placeholder="Password" type="password"/>'))
					.append($('<br><button id="comunica-save-nick">Save</button>')
						.click($.fn.comunica.saveNickClick)
					)
				)
				$.fn.comunica.supports_auth = true
			}
		}
		else if(json.evt == "auth-result"){
			$.fn.comunica.authed = json.success
			$.fn.comunica.nick = json.nick
			if(json.success){
				$('div[name="comunica-login-form"]').each(function(){$(this).remove();});
			}
		}
	}
	$.fn.comunica.inputKeyDown = function(event){
		if(event.which == 13){
			event.preventDefault();
			$('#comunica-send-message').click();
		}
	}
	$.fn.comunica.inputFocus = function(event){
		$(this).comunica.fadeDrops();
		if(!$(this).comunica.nick){
			event.preventDefault();
			$('#comunica-pick-nickname-popup').show(0, function(){$(this).trigger('shown');});
			$('#comunica-pick-nickname-input').focus();
			return;
		}
	}
	$.fn.comunica.sendClick = function(event){
		if(!$(this).comunica.nick){
			$('#comunica-pick-nickname-popup').show(0, function(){$(this).trigger('shown');});
			return;
		}
		event.preventDefault();
		var input = $('#comunica-message-input');
		var msg = input.val();
		if(!msg){return;}
		$(this).comunica.send(JSON.stringify({evt: 'message', value: msg}));
		input.val('');
	}
	$.fn.comunica.connection_closed = function(){
		$('#comunica-not-connected-popup').show();
		$.fn.comunica.fadeDrops();
	}
	$.fn.comunica.connected = function(){
		console.log("WebSocket opened");
		$('#comunica-not-connected-popup').hide();
	}
	$.fn.comunica.settingsClick = function(){
		var btnoff = $('#comunica-settings').offset();
		$('#comunica-viewers-drop').hide();
		$('#comunica-settings-drop').fadeToggle().offset({top: btnoff.top-340, left: btnoff.left-100}).focus();
	}
	$.fn.comunica.viewersClick = function(){
		var btnoff = $('#comunica-viewers').offset();
		$('#comunica-settings-drop').hide();
		if(!$('#comunica-viewers-drop').is(':visible')){
			$(this).comunica.send(JSON.stringify({'evt': 'get-viewers'}));
		}
		$('#comunica-viewers-drop').fadeToggle().offset({top: btnoff.top-340, left: btnoff.left-100});
	}
	$.fn.comunica.saveNickClick = function(){
		if($(this).comunica.supports_auth)
		{
			var nick = $('#comunica-pick-nickname-popup > .comunica-pick-nick > center > div > input[name="comunica-login-username"]').val();
			console.log(nick);
			if(nick)
			{
				var pass = $('#comunica-pick-nickname-popup > .comunica-pick-nick > center > div > input[name="comunica-login-password"]').val();
				$(this).comunica.send(JSON.stringify({evt: 'authenticate', username: nick, password: pass}));
				$('#comunica-pick-nickname-popup').hide();
				return;
			}
		}
		$(this).comunica.pickNick();
	}
	$.fn.comunica.pickNick = function(){
		var nick = $('#comunica-pick-nickname-input').val();
		if(!nick){
			alert("Nickname can not be empty");
			return;
		}
		$(this).comunica.send(JSON.stringify({evt: 'set-nick', value: nick}));
		$(this).comunica.nick = nick;
		$('#comunica-pick-nickname-popup').hide();
	}
	$.fn.comunica.setColor = function(){
		var color = $(this).css('background-color');
		$('#comunica-settings-drop > .colors > .active').removeClass('active');
		$(this).comunica.send(JSON.stringify({evt: 'set-color', value: color}));
		$(this).addClass('active');
	}
	$.fn.comunica.fadeDrops = function(){
		if($('#comunica-viewers-drop').is(':visible')){
			$('#comunica-viewers-drop').fadeOut();
		}
		if($('#comunica-settings-drop').is(':visible')){
			$('#comunica-settings-drop').fadeOut();
		}
	}
}(jQuery));