'use strict';

const knex = require('../lib/knex');
const { filterObject, enforce } = require('../lib/utils');
const config = require('../lib/config');
const log = require('../lib/log');

async function getAllUsers() {
    return await knex.transaction(async tx => {
        return await tx('user');
    });
}

async function createUser(sso, role) {
    await knex.transaction(async tx => {
        const existing = await tx('user').where({ sso }).first();
        if (existing)
            log.info("models.users", "User is already created in the system.")
        else {
            const insertUser = await tx('user').insert({ sso, role });
            log.info("models.users", insertUser)
        }

    })
}

async function deleteUser(sso) {
    enforce(sso != "ADMIN" && sso != "FXX_USER", 'Pre-defined users cannot be deleted');

    await knex.transaction(async tx => {
        await tx('user').where('sso', sso).del();
    });

}

async function setAgree(sso) {
    await knex.transaction(async tx => {
        await tx('user').where('sso', sso).update({ agree: 1 });
    });

}
module.exports.getAllUsers = getAllUsers
module.exports.createUser = createUser
module.exports.deleteUser = deleteUser
module.exports.setAgree = setAgree